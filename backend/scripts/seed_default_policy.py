"""
Seed script to create default governance policy

Run this script after initial database setup to create a default governance policy.

Usage:
    python -m backend.scripts.seed_default_policy
"""

import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from app.database.session import engine, SessionLocal
from app.models.governance_policy import GovernancePolicy


def seed_default_policy():
    """Create default governance policy if none exists"""
    
    db: Session = SessionLocal()
    
    try:
        # Check if any policy already exists
        existing_policy = db.query(GovernancePolicy).filter(GovernancePolicy.active == True).first()
        
        if existing_policy:
            print(f"✓ Active policy already exists: '{existing_policy.name}'")
            print(f"  - Max MRI: {existing_policy.max_allowed_mri}")
            print(f"  - Max Disparity: {existing_policy.max_allowed_disparity}")
            print(f"  - Approval Required Above MRI: {existing_policy.approval_required_above_mri}")
            return
        
        # Create default policy
        default_policy = GovernancePolicy(
            name="Default Production Policy",
            max_allowed_mri=80.0,              # Block models with MRI > 80
            max_allowed_disparity=0.15,        # Flag models with disparity > 15%
            approval_required_above_mri=60.0,  # Require approval for MRI > 60
            active=True
        )
        
        db.add(default_policy)
        db.commit()
        db.refresh(default_policy)
        
        print("✓ Default governance policy created successfully!")
        print(f"  - ID: {default_policy.id}")
        print(f"  - Name: {default_policy.name}")
        print(f"  - Max MRI (blocking): {default_policy.max_allowed_mri}")
        print(f"  - Max Disparity (at-risk): {default_policy.max_allowed_disparity}")
        print(f"  - Approval Required Above MRI: {default_policy.approval_required_above_mri}")
        print(f"  - Active: {default_policy.active}")
        print(f"  - Created: {default_policy.created_at}")
        
    except Exception as e:
        print(f"✗ Error creating default policy: {e}")
        db.rollback()
        raise
    
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("DriftGuardAI 2.0 - Governance Policy Seeding")
    print("=" * 60)
    print()
    
    seed_default_policy()
    
    print()
    print("=" * 60)
    print("Seeding complete!")
    print("=" * 60)
