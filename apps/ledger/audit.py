
from .models import Auditlog

def log_action(action,user_id=None,reference_id=None,metadata=None):
    print("🔥 AUDIT LOG TRIGGERED") 
    Auditlog.objects.create(
        action=action,
        user_id=user_id,
        reference_id=reference_id,
        metadata=metadata or {}
    )