"""Optional blueprint scaffold (not wired) for future split of routes.
Kept minimal to satisfy structure checklist without altering behavior.
"""

from flask import Blueprint

api = Blueprint('api', __name__)

# Example placeholder route (commented):
# @api.get('/v1/health')
# def health():
#     return {"ok": True}
