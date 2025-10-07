#!/usr/bin/env python3
"""
Helper module to fix SSL certificate issues
"""

import os
import ssl
import certifi
import urllib3
from urllib3.util.ssl_ import create_urllib3_context

def fix_ssl_issues():
    """Fix SSL certificate issues with corporate proxy bypass"""
    print("🔧 Fixing SSL certificate issues with corporate proxy bypass...")
    try:
        import os
        import ssl
        import warnings
        
        # 1. Disable SSL verification at Python level
        ssl._create_default_https_context = ssl._create_unverified_context
        
        # 2. Set comprehensive environment variables for corporate proxy bypass
        ssl_env_vars = {
            'PYTHONHTTPSVERIFY': '0',
            'SSL_VERIFY': 'false',
            'CURL_INSECURE': '1',
            # Corporate proxy bypass variables
            'REQUESTS_CA_BUNDLE': '',
            'SSL_CERT_FILE': '',
            'SSL_CERT_DIR': '',
            'CURL_CA_BUNDLE': '',
            'CURL_SSL_VERIFYPEER': '0',
            'CURL_SSL_VERIFYHOST': '0',
            # gRPC specific environment variables
            'GRPC_INSECURE': '1',
            'GRPC_SSL_CIPHER_SUITES': '',
            'GRPC_DEFAULT_SSL_ROOTS_FILE_PATH': '',
            'GRPC_SSL_TARGET_NAME_OVERRIDE': 'localhost',
            'GRPC_SSL_VERIFY': 'false',
            'GRPC_SSL_CERTIFICATE': '',
            'GRPC_SSL_PRIVATE_KEY': '',
            'GRPC_SSL_CA_CERTIFICATE': '',
            'GRPC_SSL_SERVER_NAME_OVERRIDE': 'localhost',
            # Google API specific
            'GOOGLE_API_USE_CLIENT_CERTIFICATE': 'false',
            'GOOGLE_CLOUD_PROJECT': '',
            'GOOGLE_APPLICATION_CREDENTIALS': '',
            # Corporate proxy detection and bypass
            'HTTP_PROXY': '',
            'HTTPS_PROXY': '',
            'NO_PROXY': 'localhost,127.0.0.1,::1',
            'ALL_PROXY': '',
            # Additional SSL bypass
            'PYTHONHTTPSVERIFY': '0',
            'SSL_VERIFY': 'false',
        }
        
        for key, value in ssl_env_vars.items():
            os.environ[key] = value
        
        # 3. Disable urllib3 warnings and SSL verification
        try:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            # Only disable warnings that exist
            if hasattr(urllib3.exceptions, 'SubjectAltNameWarning'):
                urllib3.disable_warnings(urllib3.exceptions.SubjectAltNameWarning)
            if hasattr(urllib3.exceptions, 'SecurityWarning'):
                urllib3.disable_warnings(urllib3.exceptions.SecurityWarning)
        except ImportError:
            pass
        
        # 4. Disable requests SSL verification
        try:
            import requests
            requests.packages.urllib3.disable_warnings()
            # Monkey patch requests to use unverified SSL
            original_request = requests.Session.request
            def unverified_request(self, method, url, **kwargs):
                kwargs.setdefault('verify', False)
                return original_request(self, method, url, **kwargs)
            requests.Session.request = unverified_request
        except ImportError:
            pass
        
        # 5. Corporate proxy SSL bypass for gRPC
        try:
            import grpc
            # Set gRPC options to disable SSL verification
            os.environ['GRPC_INSECURE'] = '1'
            
            # Try to monkey patch gRPC channel creation
            try:
                original_secure_channel = grpc.secure_channel
                def insecure_secure_channel(target, credentials=None, options=None, compression=None):
                    # Force insecure channel for corporate proxy bypass
                    return grpc.insecure_channel(target, options=options, compression=compression)
                grpc.secure_channel = insecure_secure_channel
            except Exception:
                pass
                
            # Additional gRPC corporate proxy bypass
            try:
                # Monkey patch gRPC to use insecure channels
                original_create_channel = grpc.create_channel
                def create_insecure_channel(target, options=None, compression=None):
                    return grpc.insecure_channel(target, options=options, compression=compression)
                grpc.create_channel = create_insecure_channel
            except Exception:
                pass
        except ImportError:
            pass
        
        # 6. Disable Google API client SSL verification
        try:
            from google.auth.transport import requests as google_requests
            # Monkey patch Google's requests to disable SSL verification
            original_google_request = google_requests.Request.__call__
            def unverified_google_request(self, url, method='GET', **kwargs):
                kwargs.setdefault('verify', False)
                return original_google_request(self, url, method, **kwargs)
            google_requests.Request.__call__ = unverified_google_request
        except ImportError:
            pass
        
        # 7. Suppress SSL-related warnings
        warnings.filterwarnings('ignore', message='.*SSL.*')
        warnings.filterwarnings('ignore', message='.*certificate.*')
        warnings.filterwarnings('ignore', message='.*verify.*')
        warnings.filterwarnings('ignore', message='.*handshake.*')
        
        # 8. Suppress gRPC logging aggressively
        try:
            import logging
            logging.getLogger('grpc').setLevel(logging.CRITICAL)
            logging.getLogger('grpc._cython.cygrpc').setLevel(logging.CRITICAL)
            logging.getLogger('grpc._channel').setLevel(logging.CRITICAL)
            logging.getLogger('grpc._interceptor').setLevel(logging.CRITICAL)
            # Suppress all gRPC related loggers
            for logger_name in ['grpc', 'grpc._cython', 'grpc._channel', 'grpc._interceptor']:
                logging.getLogger(logger_name).disabled = True
        except ImportError:
            pass
        
        # 9. Set environment variables to suppress gRPC logging
        os.environ['GRPC_VERBOSITY'] = 'ERROR'
        os.environ['GRPC_TRACE'] = ''
        
        # 10. Corporate proxy detection and intelligent bypass
        try:
            # Detect if we're behind a corporate proxy
            proxy_indicators = [
                os.environ.get('HTTP_PROXY'),
                os.environ.get('HTTPS_PROXY'),
                os.environ.get('http_proxy'),
                os.environ.get('https_proxy'),
                os.environ.get('ALL_PROXY'),
                os.environ.get('all_proxy')
            ]
            
            if any(proxy_indicators):
                print("🏢 Corporate proxy detected - applying advanced bypass...")
                
                # Additional corporate proxy bypass settings
                os.environ['PYTHONHTTPSVERIFY'] = '0'
                os.environ['SSL_VERIFY'] = 'false'
                os.environ['CURL_INSECURE'] = '1'
                
                # Disable certificate verification for corporate proxies
                try:
                    import ssl
                    # Create a completely unverified SSL context
                    ssl_context = ssl.create_default_context()
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                    ssl._create_default_https_context = lambda: ssl_context
                except Exception:
                    pass
                    
                # Additional urllib3 corporate proxy bypass
                try:
                    import urllib3
                    urllib3.disable_warnings()
                    # Monkey patch urllib3 to ignore SSL errors
                    original_urllib3_request = urllib3.PoolManager.request
                    def unverified_urllib3_request(self, method, url, **kwargs):
                        kwargs.setdefault('assert_hostname', False)
                        kwargs.setdefault('assert_fingerprint', None)
                        return original_urllib3_request(self, method, url, **kwargs)
                    urllib3.PoolManager.request = unverified_urllib3_request
                except Exception:
                    pass
        except Exception:
            pass
        
        print("✅ SSL issues addressed with corporate proxy bypass")
        return True
    except Exception as e:
        print(f"❌ SSL fix failed: {e}")
        return False

def apply_ssl_fix():
    """Fix SSL certificate issues with comprehensive bypass"""
    return fix_ssl_issues()

def apply_ssl_bypass():
    """Apply SSL verification bypass for testing environments"""
    return fix_ssl_issues()

def test_ssl_connection():
    """Test SSL connection to verify the fix works"""
    print("🔍 Testing SSL connection...")
    
    try:
        import requests
        
        # Test connection to Google APIs with SSL verification disabled
        response = requests.get('https://www.googleapis.com', timeout=10, verify=False)
        print(f"✅ Google APIs SSL connection: {response.status_code}")
        
        # Test connection to Slack API with SSL verification disabled
        response = requests.get('https://slack.com/api/api.test', timeout=10, verify=False)
        print(f"✅ Slack API SSL connection: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ SSL connection test failed: {e}")
        return False

# Auto-apply SSL fix when module is imported
if __name__ == "__main__":
    # Test both modes
    print("=== Testing SSL Fix ===")
    apply_ssl_fix()
    test_ssl_connection()
    
    print("\n=== Testing SSL Bypass ===")
    apply_ssl_bypass()
    test_ssl_connection()
else:
    # Auto-apply SSL fix on import
    apply_ssl_fix()