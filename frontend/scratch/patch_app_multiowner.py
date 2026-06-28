import re

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

hierarchical_block = """                      // Check hierarchical rules
                      const isOwnerEditingSelf = myRole === 'owner' && targetRole === 'owner';
                      const isOwnerEditingOther = myRole === 'owner' && targetRole !== 'owner';
                      const isAdminEditingMember = myRole === 'admin' && targetRole === 'member';
                      const isEditable = isOwnerEditingOther || isAdminEditingMember;"""

new_hierarchical_block = """                      // Check hierarchical rules
                      const isOwnerEditingSelf = myRole === 'owner' && selectedPermissionMember.user.email === currentUser.email;
                      const isOwnerEditingOther = myRole === 'owner' && !isOwnerEditingSelf;
                      const isAdminEditingMember = myRole === 'admin' && targetRole === 'member';
                      const isEditable = isOwnerEditingOther || isAdminEditingMember;"""

content = content.replace(hierarchical_block, new_hierarchical_block)


dropdown_block = """                            {/* Role management switcher if owner */}
                            {myRole === 'owner' && targetRole !== 'owner' && ("""

new_dropdown_block = """                            {/* Role management switcher if owner */}
                            {myRole === 'owner' && !isOwnerEditingSelf && ("""

content = content.replace(dropdown_block, new_dropdown_block)


transfer_option = """<option value="owner">Transfer Ownership</option>"""
new_transfer_option = """<option value="owner">Promote to Owner</option>"""
content = content.replace(transfer_option, new_transfer_option)

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("App.jsx patched for frontend multi-owner UI logic")
