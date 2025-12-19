#!/usr/bin/env python3
"""
View audit logs from the database
Usage: python view_audit_logs.py [--limit N] [--action ACTION] [--user USERNAME]
"""
from app import create_app, db
from app.models import AuditLog
import sys

app = create_app()

def view_logs(limit=50, action=None, username=None):
    with app.app_context():
        query = AuditLog.query
        
        # Filter by action if specified
        if action:
            query = query.filter_by(action=action)
        
        # Filter by username if specified
        if username:
            query = query.filter_by(username=username)
        
        # Order by most recent first
        logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
        
        if not logs:
            print("No audit logs found.")
            return
        
        print(f"\n{'='*120}")
        print(f"{'AUDIT LOGS':<120}")
        print(f"{'='*120}")
        print(f"{'Timestamp':<20} {'User':<15} {'Action':<20} {'Status':<10} {'IP Address':<15} {'Details':<40}")
        print(f"{'-'*120}")
        
        for log in logs:
            timestamp = log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            user = log.username or 'Anonymous'
            details = (log.details[:37] + '...') if log.details and len(log.details) > 40 else (log.details or '')
            
            print(f"{timestamp:<20} {user:<15} {log.action:<20} {log.status:<10} {log.ip_address or 'N/A':<15} {details:<40}")
        
        print(f"{'-'*120}")
        print(f"Total logs shown: {len(logs)}")
        print(f"{'='*120}\n")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='View audit logs')
    parser.add_argument('--limit', type=int, default=50, help='Number of logs to show (default: 50)')
    parser.add_argument('--action', type=str, help='Filter by action type')
    parser.add_argument('--user', type=str, help='Filter by username')
    
    args = parser.parse_args()
    
    view_logs(limit=args.limit, action=args.action, username=args.user)
