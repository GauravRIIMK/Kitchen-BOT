#!/usr/bin/env python3
"""
Cloud-Based Kitchen Reporter Bot
Deployed on Railway.app for 24/7 operation
Runs independently of laptop/internet status
"""

import os
import sys
import time
import signal
import threading
import sqlite3
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
import pytz

class CloudBotManager:
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.log_file = self.project_dir / "cloud_bot.log"
        self.pid_file = self.project_dir / "cloud_bot.pid"
        self.running = False
        self.ist = pytz.timezone('Asia/Kolkata')
        self.slack_token = os.environ.get("SLACK_APP_TOKEN")
        self.slack_channel = os.environ.get("SLACK_CHANNEL_ID", "C09EBE0DEUX")
        
    def log(self, message):
        """Log message with timestamp"""
        timestamp = datetime.now(self.ist).strftime("%Y-%m-%d %H:%M:%S IST")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        with open(self.log_file, "a") as f:
            f.write(log_message + "\n")
    
    def check_environment(self):
        """Check if environment is properly set up"""
        self.log("🔍 Checking cloud environment setup...")
        
        # Check required environment variables
        if not self.slack_token:
            self.log("❌ SLACK_APP_TOKEN not found!")
            return False
        
        # Check database
        if not (self.project_dir / "kitchen_reports.db").exists():
            self.log("❌ Database not found! Creating...")
            try:
                import subprocess
                result = subprocess.run([sys.executable, "db_setup.py"], 
                                      cwd=self.project_dir, 
                                      capture_output=True, text=True)
                if result.returncode != 0:
                    self.log(f"❌ Database setup failed: {result.stderr}")
                    return False
                self.log("✅ Database setup completed")
            except Exception as e:
                self.log(f"❌ Database setup error: {e}")
                return False
        
        self.log("✅ Cloud environment check passed")
        return True
    
    def setup_ssl_bypass(self):
        """Setup SSL bypass for cloud environment"""
        self.log("🔧 Setting up SSL bypass for cloud...")
        
        ssl_env_vars = {
            'PYTHONHTTPSVERIFY': '0',
            'SSL_VERIFY': 'false',
            'CURL_INSECURE': '1',
            'GRPC_INSECURE': '1',
            'GRPC_SSL_VERIFY': 'false',
            'GRPC_VERBOSITY': 'ERROR',
            'GRPC_TRACE': '',
            'REQUESTS_CA_BUNDLE': '',
            'SSL_CERT_FILE': '',
            'SSL_CERT_DIR': '',
            'CURL_CA_BUNDLE': '',
            'CURL_SSL_VERIFYPEER': '0',
            'CURL_SSL_VERIFYHOST': '0',
            'USE_GOOGLE_SHEETS': 'false'
        }
        
        for key, value in ssl_env_vars.items():
            os.environ[key] = value
        
        # Disable SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        self.log("✅ SSL bypass configured for cloud")
    
    def get_all_responsible_users(self):
        """Get all responsible users from database"""
        try:
            with sqlite3.connect("kitchen_reports.db") as con:
                cur = con.cursor()
                cur.execute("SELECT DISTINCT slack_user_id FROM responsibilities")
                return [row[0] for row in cur.fetchall()]
        except Exception as e:
            self.log(f"❌ Error getting responsible users: {e}")
            return []
    
    def get_submitted_users_today(self):
        """Get users who submitted today"""
        try:
            with sqlite3.connect("kitchen_reports.db") as con:
                cur = con.cursor()
                cur.execute("""
                    SELECT DISTINCT user_id FROM submissions 
                    WHERE DATE(submission_ts) = DATE('now')
                """)
                return [row[0] for row in cur.fetchall()]
        except Exception as e:
            self.log(f"❌ Error getting submitted users: {e}")
            return []
    
    def send_slack_message(self, text, blocks=None):
        """Send message to Slack using direct API"""
        try:
            url = "https://slack.com/api/chat.postMessage"
            headers = {
                "Authorization": f"Bearer {self.slack_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "channel": self.slack_channel,
                "text": text
            }
            
            if blocks:
                payload["blocks"] = blocks
            
            response = requests.post(url, headers=headers, json=payload, verify=False)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    return True
                else:
                    self.log(f"❌ Slack API error: {result.get('error')}")
                    return False
            else:
                self.log(f"❌ HTTP error: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error sending Slack message: {e}")
            return False
    
    def post_daily_form(self):
        """Post daily form at 00:01 IST"""
        try:
            self.log("📝 [CLOUD SCHEDULER] Starting daily form post")
            
            # Get all responsible users
            responsible_users = self.get_all_responsible_users()
            user_tags = ' '.join([f'<@{user_id}>' for user_id in responsible_users])
            
            # Create the form message
            text = f"🍽️ *Daily Kitchen Report Form - {datetime.now(self.ist).strftime('%Y-%m-%d')}*"
            
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Good morning! Please submit your kitchen report for today.\n\n*Responsible Members:* {user_tags}"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Fill Report"},
                            "style": "primary",
                            "action_id": "open_report_form_button"
                        }
                    ]
                }
            ]
            
            if self.send_slack_message(text, blocks):
                self.log("✅ [CLOUD SCHEDULER] Daily form posted successfully")
            else:
                self.log("❌ [CLOUD SCHEDULER] Failed to post daily form")
            
        except Exception as e:
            self.log(f"❌ [CLOUD SCHEDULER ERROR] Error posting daily form: {e}")
    
    def send_reminders(self):
        """Send reminders at 07:00 IST"""
        try:
            self.log("🔔 [CLOUD SCHEDULER] Starting reminder check")
            
            all_users = set(self.get_all_responsible_users())
            submitted_users = set(self.get_submitted_users_today())
            missing_users = all_users - submitted_users
            
            if not missing_users:
                self.log("✅ [CLOUD SCHEDULER] All reports submitted. No reminder needed.")
                return
            
            user_tags = ' '.join([f'<@{user_id}>' for user_id in missing_users])
            message = f"🔔 *Reminder!* The following members have not submitted their report. Submissions close at 8:00 AM.\n{user_tags}"
            
            if self.send_slack_message(message):
                self.log("✅ [CLOUD SCHEDULER] Reminders sent successfully")
            else:
                self.log("❌ [CLOUD SCHEDULER] Failed to send reminders")
            
        except Exception as e:
            self.log(f"❌ [CLOUD SCHEDULER ERROR] Error sending reminders: {e}")
    
    def post_status_report(self):
        """Post status report at 08:30 IST"""
        try:
            self.log("📊 [CLOUD SCHEDULER] Starting status report")
            
            with sqlite3.connect("kitchen_reports.db") as con:
                cur = con.cursor()
                
                # Get all responsible users
                cur.execute("SELECT DISTINCT slack_user_id FROM responsibilities")
                all_responsible = [row[0] for row in cur.fetchall()]
                
                # Get today's submissions
                cur.execute("""
                    SELECT user_id, kitchen_name, report_text, submission_ts
                    FROM submissions 
                    WHERE DATE(submission_ts) = DATE('now')
                    ORDER BY submission_ts DESC
                """)
                submissions = cur.fetchall()
            
            total_responsible = len(all_responsible)
            total_submitted = len(submissions)
            missing_count = total_responsible - total_submitted
            
            # Create status report
            status_text = f"📊 *Daily Kitchen Report Status - {datetime.now(self.ist).strftime('%Y-%m-%d')}*\n\n"
            status_text += f"• *Total Responsible:* {total_responsible}\n"
            status_text += f"• *Reports Submitted:* {total_submitted}\n"
            status_text += f"• *Missing Reports:* {missing_count}\n"
            status_text += f"• *Completion Rate:* {(total_submitted/total_responsible*100):.1f}%" if total_responsible > 0 else "0%"
            
            if submissions:
                status_text += f"\n\n📝 *Today's Submissions:*\n"
                for sub in submissions:
                    status_text += f"• <@{sub[0]}> - {sub[1]} ({sub[3][:16]})\n"
            
            if self.send_slack_message(status_text):
                self.log("✅ [CLOUD SCHEDULER] Status report posted successfully")
            else:
                self.log("❌ [CLOUD SCHEDULER] Failed to post status report")
            
        except Exception as e:
            self.log(f"❌ [CLOUD SCHEDULER ERROR] Error posting status report: {e}")
    
    def run_scheduler(self):
        """Run the cloud scheduler"""
        self.log("⏰ Starting cloud scheduler...")
        
        while self.running:
            try:
                now = datetime.now(self.ist)
                current_time = now.strftime("%H:%M")
                
                # Check if it's time for scheduled tasks
                if current_time == "00:01":
                    self.post_daily_form()
                elif current_time == "07:00":
                    self.send_reminders()
                elif current_time == "08:30":
                    self.post_status_report()
                
                # Log every hour for monitoring
                if now.minute == 0:
                    self.log(f"🕐 Cloud bot running - Next: {self.get_next_scheduled_time()}")
                
                # Sleep for 1 minute
                time.sleep(60)
                
            except Exception as e:
                self.log(f"❌ Scheduler error: {e}")
                time.sleep(60)
    
    def get_next_scheduled_time(self):
        """Get next scheduled execution time"""
        now = datetime.now(self.ist)
        today = now.date()
        
        times = [
            self.ist.localize(datetime.combine(today, datetime.min.time().replace(hour=0, minute=1))),
            self.ist.localize(datetime.combine(today, datetime.min.time().replace(hour=7, minute=0))),
            self.ist.localize(datetime.combine(today, datetime.min.time().replace(hour=8, minute=30)))
        ]
        
        # Add tomorrow's times if all today's times have passed
        if now.time() > datetime.min.time().replace(hour=8, minute=30):
            tomorrow = today + timedelta(days=1)
            times = [
                self.ist.localize(datetime.combine(tomorrow, datetime.min.time().replace(hour=0, minute=1))),
                self.ist.localize(datetime.combine(tomorrow, datetime.min.time().replace(hour=7, minute=0))),
                self.ist.localize(datetime.combine(tomorrow, datetime.min.time().replace(hour=8, minute=30)))
            ]
        
        # Find next time
        for time in times:
            if time > now:
                return time.strftime("%H:%M IST")
        
        return "Tomorrow 00:01 IST"
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.log(f"📡 Received signal {signum}")
        self.stop()
        sys.exit(0)
    
    def stop(self):
        """Stop the cloud bot manager"""
        self.log("🛑 Stopping Cloud Bot Manager...")
        self.running = False
        
        if self.pid_file.exists():
            self.pid_file.unlink()
    
    def run(self):
        """Main run loop"""
        self.log("☁️ Kitchen Reporter Bot - Cloud Manager")
        self.log("=" * 60)
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            # Check environment
            if not self.check_environment():
                self.log("❌ Environment check failed")
                return False
            
            # Setup SSL bypass
            self.setup_ssl_bypass()
            
            # Save PID
            with open(self.pid_file, "w") as f:
                f.write(str(os.getpid()))
            
            self.running = True
            
            # Start scheduler in a separate thread
            scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
            scheduler_thread.start()
            
            self.log("✅ Cloud scheduler started")
            self.log("📅 Scheduled Times (IST): 00:01 (Form), 07:00 (Reminder), 08:30 (Status)")
            self.log(f"🌐 Cloud Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'Local')}")
            self.log(f"⏰ Next Execution: {self.get_next_scheduled_time()}")
            
            # Keep main thread alive
            while self.running:
                time.sleep(1)
            
        except KeyboardInterrupt:
            self.log("👋 Shutdown requested by user")
        except Exception as e:
            self.log(f"❌ Unexpected error: {e}")
        finally:
            self.stop()

def main():
    """Main function"""
    manager = CloudBotManager()
    manager.run()

if __name__ == "__main__":
    main()
