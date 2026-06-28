import base64
import datetime
import logging
import re
import uuid
import zlib
from datetime import timezone
from xml.etree import ElementTree as ET

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

from .models import SAMLConfiguration

logger = logging.getLogger(__name__)
User = get_user_model()


def deflate_and_base64(xml_string):
    """Compress XML string using DEFLATE (raw) and encode to base64."""
    compressor = zlib.compressobj(zlib.Z_DEFAULT_COMPRESSION, zlib.DEFLATED, -15)
    compressed = compressor.compress(xml_string.encode("utf-8"))
    compressed += compressor.flush()
    return base64.b64encode(compressed).decode("utf-8")


def parse_saml_response(saml_response_b64):
    """Decode and parse the SAML XML assertion."""
    try:
        saml_xml = base64.b64decode(saml_response_b64).decode("utf-8")
        root = ET.fromstring(saml_xml)
    except Exception as e:
        logger.error(f"SAML XML parse error: {e}")
        return None, None, None, None, None

    ns = {
        "samlp": "urn:oasis:names:tc:SAML:2.0:protocol",
        "saml": "urn:oasis:names:tc:SAML:2.0:assertion",
        "ds": "http://www.w3.org/2000/09/xmldsig#",
    }

    # Find Issuer
    issuer = root.find(".//saml:Issuer", ns)
    if issuer is None:
        # Try finding at root level or without prefix
        issuer = root.find("Issuer")
    issuer_val = issuer.text.strip() if issuer is not None and issuer.text else None

    # Find NameID
    name_id = root.find(".//saml:NameID", ns)
    email = name_id.text.strip() if name_id is not None and name_id.text else None

    first_name = None
    last_name = None

    # Try attribute values
    for attr in root.findall(".//saml:Attribute", ns):
        attr_name = attr.get("Name")
        val_node = attr.find("saml:AttributeValue", ns)
        if val_node is None or not val_node.text:
            continue
        val_text = val_node.text.strip()

        if attr_name in [
            "email",
            "mail",
            "User.Email",
            "emailaddress",
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
        ]:
            if not email or "@" not in email:
                if "@" in val_text:
                    email = val_text
        elif attr_name in [
            "first_name",
            "firstName",
            "givenName",
            "givenname",
            "User.FirstName",
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname",
        ]:
            first_name = val_text
        elif attr_name in [
            "last_name",
            "lastName",
            "surName",
            "surname",
            "sn",
            "User.LastName",
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname",
        ]:
            last_name = val_text

    return issuer_val, email, first_name, last_name, saml_xml


def verify_xml_signature(raw_xml_str, x509_cert_pem):
    """Verify SAML Signature block using pure Python cryptography module."""
    try:
        # Format X509 PEM certificate correctly
        cert_body = (
            x509_cert_pem.replace("-----BEGIN CERTIFICATE-----", "")
            .replace("-----END CERTIFICATE-----", "")
            .replace("\n", "")
            .replace("\r", "")
            .strip()
        )
        cert_pem = f"-----BEGIN CERTIFICATE-----\n{cert_body}\n-----END CERTIFICATE-----"
        cert = x509.load_pem_x509_certificate(cert_pem.encode("utf-8"), default_backend())
        public_key = cert.public_key()

        # Find the SignedInfo and SignatureValue blocks
        signed_info_match = re.search(r"<ds:SignedInfo.*?>.*?</ds:SignedInfo>", raw_xml_str, re.DOTALL)
        sig_value_match = re.search(r"<ds:SignatureValue.*?>(.*?)</ds:SignatureValue>", raw_xml_str, re.DOTALL)

        if not signed_info_match or not sig_value_match:
            # Fallback for without ds: namespace prefix
            signed_info_match = re.search(r"<SignedInfo.*?>.*?</SignedInfo>", raw_xml_str, re.DOTALL)
            sig_value_match = re.search(r"<SignatureValue.*?>(.*?)</SignatureValue>", raw_xml_str, re.DOTALL)

        if not signed_info_match or not sig_value_match:
            logger.error("SAML Response missing SignedInfo or SignatureValue tags")
            return False

        signed_info_bytes = signed_info_match.group(0).encode("utf-8")
        signature_b64 = sig_value_match.group(1).replace("\n", "").replace("\r", "").strip()
        signature_bytes = base64.b64decode(signature_b64)

        # Standard algorithms used by modern Identity Providers
        for hash_alg in [hashes.SHA256(), hashes.SHA1()]:
            try:
                public_key.verify(
                    signature_bytes,
                    signed_info_bytes,
                    padding.PKCS1v15(),
                    hash_alg,
                )
                return True
            except Exception:
                continue
        logger.error("Cryptographic signature verification failed for all digest algorithms")
        return False
    except Exception as e:
        logger.error(f"SAML Signature Verification exception: {e}")
        return False


class SAMLLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, config_id):
        config = get_object_or_404(SAMLConfiguration, id=config_id, is_active=True)
        
        # Build SP URLs
        acs_url = request.build_absolute_uri(reverse("saml-acs"))
        sp_entity_id = request.build_absolute_uri("/")

        # Generate SAML AuthnRequest XML
        request_id = f"_{uuid.uuid4().hex}"
        from datetime import timezone as dt_timezone
        issue_instant = datetime.datetime.now(dt_timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        authn_request = f"""<samlp:AuthnRequest xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
                    xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
                    ID="{request_id}"
                    Version="2.0"
                    IssueInstant="{issue_instant}"
                    Destination="{config.sso_url}"
                    AssertionConsumerServiceURL="{acs_url}"
                    ProtocolBinding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST">
    <saml:Issuer>{sp_entity_id}</saml:Issuer>
    <samlp:NameIDPolicy Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
                        AllowCreate="true"/>
</samlp:AuthnRequest>"""

        saml_request_b64 = deflate_and_base64(authn_request)
        relay_state = str(config.id)

        # Check if Mock SAML Identity Provider is configured
        is_mock = (config.entity_id == "mock-idp") or getattr(settings, "SAML_MOCK_ALL", False)
        
        if is_mock:
            mock_idp_url = request.build_absolute_uri(reverse("saml-mock-idp"))
            redirect_url = f"{mock_idp_url}?config_id={config.id}&SAMLRequest={saml_request_b64}&RelayState={relay_state}"
        else:
            redirect_url = f"{config.sso_url}?SAMLRequest={saml_request_b64}&RelayState={relay_state}"

        return HttpResponseRedirect(redirect_url)


@method_decorator(csrf_exempt, name="dispatch")
class SAMLACSView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        saml_response = request.data.get("SAMLResponse")
        relay_state = request.data.get("RelayState")

        if not saml_response:
            return Response({"error": "SAMLResponse POST payload is missing"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Parse response attributes
        issuer_val, email, parsed_first_name, parsed_last_name, raw_xml_str = parse_saml_response(saml_response)
        
        if not email:
            return Response({"error": "Failed to parse email attribute/NameID from SAML response"}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Look up SAML configuration
        config = None
        if relay_state:
            try:
                config = SAMLConfiguration.objects.get(id=relay_state, is_active=True)
            except (SAMLConfiguration.DoesNotExist, ValueError):
                pass
        
        if not config and issuer_val:
            config = SAMLConfiguration.objects.filter(entity_id=issuer_val, is_active=True).first()

        if not config:
            return Response({"error": f"SAML Configuration not found for Issuer: {issuer_val}"}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Verify Signature unless Mock IdP is used
        is_mock = (config.entity_id == "mock-idp") or (issuer_val == "mock-idp")
        if not is_mock:
            if not config.x509_certificate:
                return Response({"error": "X.509 verification certificate is not configured for live SSO"}, status=status.HTTP_400_BAD_REQUEST)
            
            sig_valid = verify_xml_signature(raw_xml_str, config.x509_certificate)
            if not sig_valid:
                return Response({"error": "Invalid cryptographic signature in SAML Response"}, status=status.HTTP_401_UNAUTHORIZED)

        # 4. User Provisioning
        first_name = parsed_first_name or request.data.get("first_name") or "SSO"
        last_name = parsed_last_name or request.data.get("last_name") or "User"
        
        user, created = User.objects.get_or_create(
            email=email.lower(),
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "is_active": True,
                "must_change_password": False,
            }
        )

        if created:
            user.set_unusable_password()
            user.save()
            try:
                from notifications.organization import process_pending_invitations_for_new_user
                process_pending_invitations_for_new_user(user)
            except Exception as e:
                logger.error(f"Error processing pending invitations: {e}")

        # If multiple active organizations, check membership
        # For now, auto-assign user to the SAML config's organization if defined
        if config.organization:
            from organizations.models import OrganizationMembership
            OrganizationMembership.objects.get_or_create(
                organization=config.organization,
                user=user,
                defaults={"role": "member"}
            )

        # 5. Generate SimpleJWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # Redirect back to frontend with tokens
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
        redirect_url = f"{frontend_url}/?access={access_token}&refresh={refresh_token}"
        return HttpResponseRedirect(redirect_url)


class SAMLLogoutView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # Optional logout endpoint: redirect to IdP's logout URL, or redirect to home page
        config_id = request.GET.get("config_id")
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
        
        if config_id:
            try:
                config = SAMLConfiguration.objects.get(id=config_id)
                if config.logout_url:
                    return HttpResponseRedirect(config.logout_url)
            except (SAMLConfiguration.DoesNotExist, ValueError):
                pass
        
        return HttpResponseRedirect(f"{frontend_url}/")


class SAMLMockIdPView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        config_id = request.GET.get("config_id", "")
        saml_request = request.GET.get("SAMLRequest", "")
        relay_state = request.GET.get("RelayState", "")
        manual = request.GET.get("manual", "false").lower() == "true"

        try:
            config = SAMLConfiguration.objects.get(id=config_id)
            company_name = config.company_name
        except Exception:
            company_name = "Mock Tenant"

        if not manual:
            # Auto-submit immediately using default developer credentials
            email = request.GET.get("email", "sso_developer@acme.com")
            first_name = request.GET.get("first_name", "SSO")
            last_name = request.GET.get("last_name", "Developer")

            # Create mock SAMLResponse XML
            acs_url = request.build_absolute_uri(reverse("saml-acs"))
            from datetime import timezone as dt_timezone
            issue_instant = datetime.datetime.now(dt_timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            assertion_id = f"_{uuid.uuid4().hex}"
            response_id = f"_{uuid.uuid4().hex}"

            mock_xml = f"""<samlp:Response xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
                    xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
                    ID="{response_id}"
                    Version="2.0"
                    IssueInstant="{issue_instant}"
                    Destination="{acs_url}">
        <samlp:Status>
            <samlp:StatusCode Value="urn:oasis:names:tc:SAML:2.0:status:Success"/>
        </samlp:Status>
        <saml:Assertion Version="2.0"
                        ID="{assertion_id}"
                        IssueInstant="{issue_instant}">
            <saml:Issuer>mock-idp</saml:Issuer>
            <saml:Subject>
                <saml:NameID Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress">{email}</saml:NameID>
            </saml:Subject>
            <saml:AttributeStatement>
                <saml:Attribute Name="email">
                    <saml:AttributeValue>{email}</saml:AttributeValue>
                </saml:Attribute>
                <saml:Attribute Name="first_name">
                    <saml:AttributeValue>{first_name}</saml:AttributeValue>
                </saml:Attribute>
                <saml:Attribute Name="last_name">
                    <saml:AttributeValue>{last_name}</saml:AttributeValue>
                </saml:Attribute>
            </saml:AttributeStatement>
        </saml:Assertion>
    </samlp:Response>"""

            saml_response_b64 = base64.b64encode(mock_xml.encode("utf-8")).decode("utf-8")
            
            html_autosubmit = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Redirecting to ParseOps...</title>
                <style>
                    body {{
                        font-family: 'Inter', system-ui, -apple-system, sans-serif;
                        background: #0f172a;
                        color: #f8fafc;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                    }}
                    .spinner {{
                        border: 4px solid rgba(255, 255, 255, 0.1);
                        width: 36px;
                        height: 36px;
                        border-radius: 50%;
                        border-left-color: #6366f1;
                        animation: spin 1s linear infinite;
                        margin-bottom: 1.5rem;
                    }}
                    @keyframes spin {{
                        0% {{ transform: rotate(0deg); }}
                        100% {{ transform: rotate(360deg); }}
                    }}
                    h2 {{
                        font-size: 1.25rem;
                        font-weight: 500;
                        margin: 0 0 0.5rem 0;
                    }}
                    p {{
                        color: #94a3b8;
                        font-size: 0.875rem;
                        margin: 0;
                    }}
                </style>
            </head>
            <body onload="document.forms[0].submit()">
                <div class="spinner"></div>
                <h2>Completing SSO Authentication...</h2>
                <p>Please wait while we redirect you back to ParseOps.</p>
                <form method="POST" action="{acs_url}">
                    <input type="hidden" name="SAMLResponse" value="{saml_response_b64}"/>
                    <input type="hidden" name="RelayState" value="{relay_state}"/>
                    <noscript>
                        <button type="submit">Click here to continue</button>
                    </noscript>
                </form>
            </body>
            </html>
            """
            return HttpResponse(html_autosubmit)

        # Show the manual mock page for testing
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>ParseOps Mock IDP - {company_name}</title>
            <style>
                body {{
                    font-family: 'Inter', system-ui, -apple-system, sans-serif;
                    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
                    color: #f8fafc;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }}
                .card {{
                    background: rgba(30, 41, 59, 0.7);
                    backdrop-filter: blur(16px);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 16px;
                    padding: 2.5rem;
                    width: 420px;
                    box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.5), 0 8px 10px -6px rgb(0 0 0 / 0.5);
                }}
                h2 {{
                    margin-top: 0;
                    margin-bottom: 0.5rem;
                    font-size: 1.75rem;
                    font-weight: 700;
                    background: linear-gradient(to right, #38bdf8, #818cf8);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }}
                p {{
                    color: #94a3b8;
                    font-size: 0.875rem;
                    margin-bottom: 2rem;
                }}
                .form-group {{
                    margin-bottom: 1.25rem;
                }}
                label {{
                    display: block;
                    font-size: 0.75rem;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    color: #cbd5e1;
                    margin-bottom: 0.5rem;
                }}
                input {{
                    width: 100%;
                    padding: 0.75rem 1rem;
                    background: rgba(15, 23, 42, 0.6);
                    border: 1px solid rgba(255, 255, 255, 0.15);
                    border-radius: 8px;
                    color: #f8fafc;
                    font-size: 0.95rem;
                    box-sizing: border-box;
                    transition: all 0.2s;
                }}
                input:focus {{
                    outline: none;
                    border-color: #6366f1;
                    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.3);
                }}
                button {{
                    width: 100%;
                    padding: 0.85rem;
                    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
                    border: none;
                    border-radius: 8px;
                    color: #ffffff;
                    font-weight: 600;
                    font-size: 1rem;
                    cursor: pointer;
                    margin-top: 1rem;
                    transition: transform 0.15s, opacity 0.15s;
                }}
                button:hover {{
                    transform: translateY(-1px);
                    opacity: 0.95;
                }}
                button:active {{
                    transform: translateY(0);
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <h2>Mock SAML Identity Provider</h2>
                <p>Simulating Single Sign-On for <strong>{company_name}</strong></p>
                
                <form method="POST" action="">
                    <input type="hidden" name="config_id" value="{config_id}"/>
                    <input type="hidden" name="SAMLRequest" value="{saml_request}"/>
                    <input type="hidden" name="RelayState" value="{relay_state}"/>
                    
                    <div class="form-group">
                        <label>SAML NameID (Email)</label>
                        <input type="email" name="email" value="sso_developer@acme.com" required placeholder="Enter developer email"/>
                    </div>
                    
                    <div class="form-group">
                        <label>First Name</label>
                        <input type="text" name="first_name" value="SSO" required/>
                    </div>
                    
                    <div class="form-group">
                        <label>Last Name</label>
                        <input type="text" name="last_name" value="Developer" required/>
                    </div>
                    
                    <button type="submit">Complete SSO Login</button>
                </form>
            </div>
        </body>
        </html>
        """
        return HttpResponse(html_content)

    def post(self, request):
        email = request.data.get("email", "sso_developer@acme.com")
        first_name = request.data.get("first_name", "SSO")
        last_name = request.data.get("last_name", "Developer")
        relay_state = request.data.get("RelayState", "")

        # Create mock SAMLResponse XML
        acs_url = request.build_absolute_uri(reverse("saml-acs"))
        from datetime import timezone as dt_timezone
        issue_instant = datetime.datetime.now(dt_timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        assertion_id = f"_{uuid.uuid4().hex}"
        response_id = f"_{uuid.uuid4().hex}"

        mock_xml = f"""<samlp:Response xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
                xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
                ID="{response_id}"
                Version="2.0"
                IssueInstant="{issue_instant}"
                Destination="{acs_url}">
    <samlp:Status>
        <samlp:StatusCode Value="urn:oasis:names:tc:SAML:2.0:status:Success"/>
    </samlp:Status>
    <saml:Assertion Version="2.0"
                    ID="{assertion_id}"
                    IssueInstant="{issue_instant}">
        <saml:Issuer>mock-idp</saml:Issuer>
        <saml:Subject>
            <saml:NameID Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress">{email}</saml:NameID>
        </saml:Subject>
        <saml:AttributeStatement>
            <saml:Attribute Name="email">
                <saml:AttributeValue>{email}</saml:AttributeValue>
            </saml:Attribute>
            <saml:Attribute Name="first_name">
                <saml:AttributeValue>{first_name}</saml:AttributeValue>
            </saml:Attribute>
            <saml:Attribute Name="last_name">
                <saml:AttributeValue>{last_name}</saml:AttributeValue>
            </saml:Attribute>
        </saml:AttributeStatement>
    </saml:Assertion>
</samlp:Response>"""

        saml_response_b64 = base64.b64encode(mock_xml.encode("utf-8")).decode("utf-8")
        
        # Return a self-submitting HTML form to post back to ACS endpoint
        html_autosubmit = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Completing SSO Authentication...</title>
        </head>
        <body onload="document.forms[0].submit()">
            <div style="font-family: sans-serif; text-align: center; margin-top: 100px;">
                <h2>Completing SSO Authentication...</h2>
                <p>Redirecting you back to ParseOps ACS endpoint.</p>
                <form method="POST" action="{acs_url}">
                    <input type="hidden" name="SAMLResponse" value="{saml_response_b64}"/>
                    <input type="hidden" name="RelayState" value="{relay_state}"/>
                    <input type="hidden" name="first_name" value="{first_name}"/>
                    <input type="hidden" name="last_name" value="{last_name}"/>
                    <noscript>
                        <button type="submit">Click here to continue</button>
                    </noscript>
                </form>
            </div>
        </body>
        </html>
        """
        return HttpResponse(html_autosubmit)


class SAMLConfigListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        configs = SAMLConfiguration.objects.filter(is_active=True).values("id", "company_name")
        return Response(list(configs), status=status.HTTP_200_OK)

