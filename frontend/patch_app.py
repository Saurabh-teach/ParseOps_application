import os

app_path = r"d:\test_applications\frontend\src\App.jsx"
with open(app_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace profileData defaults
content = content.replace(
"""  lunch_break_start: '13:00:00',
  lunch_break_end: '14:00:00',
  tea_break_start: '17:00:00',""",
"""  lunch_break_start: '13:00:00',
  lunch_break_end: '14:00:00',
  no_lunch_break: false,
  tea_break_start: '17:00:00',
  no_tea_break: false,""")

# Replace No Lunch Break checkbox
content = content.replace(
"""                  <input
                    type="checkbox"
                    checked={profileData.lunch_break_start === profileData.lunch_break_end}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setProfileData({ ...profileData, lunch_break_start: '00:00:00', lunch_break_end: '00:00:00' });
                      } else {
                        setProfileData({ ...profileData, lunch_break_start: '13:00:00', lunch_break_end: '14:00:00' });
                      }
                    }}
                  />
                  No Lunch Break
                </label>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', opacity: profileData.lunch_break_start === profileData.lunch_break_end ? 0.5 : 1, pointerEvents: profileData.lunch_break_start === profileData.lunch_break_end ? 'none' : 'auto' }}>""",
"""                  <input
                    type="checkbox"
                    checked={profileData.no_lunch_break}
                    onChange={(e) => {
                      setProfileData({ ...profileData, no_lunch_break: e.target.checked });
                    }}
                  />
                  No Lunch Break
                </label>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', opacity: profileData.no_lunch_break ? 0.5 : 1, pointerEvents: profileData.no_lunch_break ? 'none' : 'auto' }}>""")

# Replace No Tea Break checkbox
content = content.replace(
"""                  <input
                    type="checkbox"
                    checked={profileData.tea_break_start === profileData.tea_break_end}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setProfileData({ ...profileData, tea_break_start: '00:00:00', tea_break_end: '00:00:00' });
                      } else {
                        setProfileData({ ...profileData, tea_break_start: '17:00:00', tea_break_end: '17:30:00' });
                      }
                    }}
                  />
                  No Tea Break
                </label>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', opacity: profileData.tea_break_start === profileData.tea_break_end ? 0.5 : 1, pointerEvents: profileData.tea_break_start === profileData.tea_break_end ? 'none' : 'auto' }}>""",
"""                  <input
                    type="checkbox"
                    checked={profileData.no_tea_break}
                    onChange={(e) => {
                      setProfileData({ ...profileData, no_tea_break: e.target.checked });
                    }}
                  />
                  No Tea Break
                </label>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', opacity: profileData.no_tea_break ? 0.5 : 1, pointerEvents: profileData.no_tea_break ? 'none' : 'auto' }}>""")

# Add segments to Schedule Preview
content = content.replace(
"""          setSchedulePreview({
            message: res.message || '',
            isLoading: false,
          });""",
"""          setSchedulePreview({
            message: res.message || '',
            segments: res.segments || [],
            isLoading: false,
          });""")

with open(app_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Successfully patched App.jsx")
