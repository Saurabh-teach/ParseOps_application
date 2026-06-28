import re

with open('c:/Users/saura/ParseOps/frontend/src/api.js', 'r', encoding='utf-8') as f:
    content = f.read()

notif_block = """export const getNotifications = async () => {
  const response = await api.get('/notifications/');
  return response.data;
};"""
new_notif_block = """export const getNotifications = async (orgSlug = null, memberId = null) => {
  let url = '/notifications/';
  if (orgSlug) {
      url += `?org=${orgSlug}`;
      if (memberId) url += `&member=${memberId}`;
  }
  const response = await api.get(url);
  return response.data;
};"""
if "orgSlug = null" not in content:
    content = content.replace(notif_block, new_notif_block)

history_block = """export const getOrganizationHistory = async (orgSlug) => {
  const response = await api.get(`/${orgSlug}/history/`);
  return response.data;
};"""
new_history_block = """export const getOrganizationHistory = async (orgSlug, memberId = null) => {
  let url = `/${orgSlug}/history/`;
  if (memberId) {
      url += `?member=${memberId}`;
  }
  const response = await api.get(url);
  return response.data;
};"""
if "memberId = null" not in content:
    content = content.replace(history_block, new_history_block)

with open('c:/Users/saura/ParseOps/frontend/src/api.js', 'w', encoding='utf-8') as f:
    f.write(content)
print("api.js patched")
