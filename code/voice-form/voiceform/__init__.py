"""voiceform: speak a form in Marathi, Hindi or English; a small local pipeline fills it.

Speech -> transcript -> plain-code normalising -> small model writes field values with a quoted evidence span ->
plain-code checks -> a person confirms -> local sinks (form JSON, SQLite, CRM record, API payload file).
Offline at run time; the only server is LM Studio on localhost.
"""
