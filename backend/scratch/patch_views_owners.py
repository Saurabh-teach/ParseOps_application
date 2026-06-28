import re

with open('c:/Users/saura/ParseOps/backend/organizations/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

change_role_block = """        if new_role == 'owner':
            # Transfer ownership: only current owner can transfer ownership
            if requesting_membership.role != 'owner':
                return Response({"error": "Only the organization owner can transfer ownership."}, status=status.HTTP_403_FORBIDDEN)
                
            # Demote current owner to admin, promote target member to owner
            requesting_membership.role = 'admin'
            requesting_membership.save()
            
            membership.role = 'owner'
            membership.save()
            
            org.owner = membership.user
            org.save()
            
            return Response({"message": "Ownership transferred successfully!"}, status=status.HTTP_200_OK)
            
        # Admins cannot promote someone to admin or demote admins if they are not the owner
        if requesting_membership.role != 'owner':
            return Response({"error": "Only the owner can promote or demote administrators."}, status=status.HTTP_403_FORBIDDEN)
            
        membership.role = new_role
        membership.save()
        return Response({"message": f"Member role updated to {new_role} successfully!"}, status=status.HTTP_200_OK)"""

new_change_role_block = """        from django.core.exceptions import ValidationError
        
        if requesting_membership.role != 'owner':
            return Response({"error": "Only an organization owner can change roles."}, status=status.HTTP_403_FORBIDDEN)
            
        if new_role == 'owner':
            membership.role = 'owner'
            membership.save()
            # If org.owner is somehow tied, let's keep it sync with the first owner or do nothing.
            # We don't strictly need org.owner if we use OrganizationMembership for everything.
            return Response({"message": "Member promoted to owner successfully!"}, status=status.HTTP_200_OK)
            
        if membership.role == 'owner' and new_role != 'owner':
            if membership.user == request.user:
                return Response({"error": "You cannot demote yourself. Another owner must demote you."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                membership.role = new_role
                membership.save()
                return Response({"message": f"Owner demoted to {new_role} successfully!"}, status=status.HTTP_200_OK)
            except ValidationError as e:
                return Response({"error": str(e.messages[0]) if hasattr(e, 'messages') else str(e)}, status=status.HTTP_400_BAD_REQUEST)
                
        membership.role = new_role
        membership.save()
        return Response({"message": f"Member role updated to {new_role} successfully!"}, status=status.HTTP_200_OK)"""

content = content.replace(change_role_block, new_change_role_block)

remove_member_block = """    @action(detail=True, methods=['post'], url_path='remove-member')
    def remove_member(self, request, pk=None):
        org = self.get_object()
        member_id = request.data.get('member_id')
        
        try:
            membership = OrganizationMembership.objects.get(id=member_id, organization=org)
            
            # Simple permission check
            requesting_membership = OrganizationMembership.objects.get(organization=org, user=request.user)
            if requesting_membership.role != 'owner' and requesting_membership.role != 'admin':
                return Response({"error": "Only owners or admins can remove members."}, status=status.HTTP_403_FORBIDDEN)
                
            if membership.role == 'owner' and requesting_membership.role != 'owner':
                return Response({"error": "Admins cannot remove the owner."}, status=status.HTTP_403_FORBIDDEN)
                
            membership.is_active = False
            membership.save()
            return Response({"message": "Member removed successfully!"}, status=status.HTTP_200_OK)
        except OrganizationMembership.DoesNotExist:
            return Response({"error": "Membership not found."}, status=status.HTTP_404_NOT_FOUND)"""

new_remove_member_block = """    @action(detail=True, methods=['post'], url_path='remove-member')
    def remove_member(self, request, pk=None):
        org = self.get_object()
        member_id = request.data.get('member_id')
        
        from django.core.exceptions import ValidationError
        
        try:
            membership = OrganizationMembership.objects.get(id=member_id, organization=org)
            requesting_membership = OrganizationMembership.objects.get(organization=org, user=request.user)
            
            if requesting_membership.role not in ['owner', 'admin']:
                return Response({"error": "Only owners or admins can remove members."}, status=status.HTTP_403_FORBIDDEN)
                
            if membership.role == 'owner':
                if requesting_membership.role != 'owner':
                    return Response({"error": "Admins cannot remove an owner."}, status=status.HTTP_403_FORBIDDEN)
                if membership.user == request.user:
                    return Response({"error": "You cannot remove yourself. Another owner must remove you, or you can use the leave workspace option."}, status=status.HTTP_400_BAD_REQUEST)
                
            membership.is_active = False
            membership.save()
            return Response({"message": "Member removed successfully!"}, status=status.HTTP_200_OK)
        except OrganizationMembership.DoesNotExist:
            return Response({"error": "Membership not found."}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            return Response({"error": str(e.messages[0]) if hasattr(e, 'messages') else str(e)}, status=status.HTTP_400_BAD_REQUEST)"""

content = content.replace(remove_member_block, new_remove_member_block)

with open('c:/Users/saura/ParseOps/backend/organizations/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("views.py patched for multiple owners logic")
