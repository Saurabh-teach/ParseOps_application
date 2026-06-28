import re

with open('c:/Users/saura/ParseOps/frontend/src/api.js', 'r', encoding='utf-8') as f:
    content = f.read()

target = "export default api;"
replacement = """export const submitTaskProof = async (taskId, formData) => {
  const response = await api.post(`/tasks/${taskId}/submit/`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    }
  });
  return response.data;
};

export default api;"""

content = content.replace(target, replacement)

with open('c:/Users/saura/ParseOps/frontend/src/api.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("api.js patched to support submitTaskProof")
