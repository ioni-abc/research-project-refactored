"""
Test Script - Simulates microservice workflow
Workflow: Auth (login) → Order (place order) → Payment (process payment)
"""

import requests
import json
import time
from typing import Optional

# Service URLs
AUTH_SERVICE = "http://localhost:8001"
ORDER_SERVICE = "http://localhost:8002"  # Will exist later
PAYMENT_SERVICE = "http://localhost:8003"  # Will exist later

# Test data
TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpass"


class TestRunner:
    def __init__(self):
        self.results = []
        self.token: Optional[str] = None
    
    def log(self, message: str, status: str = "INFO"):
        """Log a message with status"""
        print(f"[{status}] {message}")
    
    def step_login(self) -> bool:
        """Step 1: Authenticate and get JWT token"""
        self.log("=== STEP 1: LOGIN ===")
        
        try:
            response = requests.post(
                f"{AUTH_SERVICE}/auth/login",
                json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.log(f"✓ Login successful", "SUCCESS")
                self.log(f"  Token: {self.token[:50]}...", "INFO")
                self.results.append(("login", "success", response.elapsed.total_seconds()))
                return True
            else:
                self.log(f"✗ Login failed: {response.status_code}", "ERROR")
                self.results.append(("login", "failed", 0))
                return False
        
        except requests.exceptions.RequestException as e:
            self.log(f"✗ Login error: {e}", "ERROR")
            self.results.append(("login", "error", 0))
            return False
    
    def step_place_order(self) -> bool:
        """Step 2: Place an order (requires token)"""
        self.log("\n=== STEP 2: PLACE ORDER ===")
        
        if not self.token:
            self.log("✗ No token available", "ERROR")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            order_data = {
                "user_id": TEST_USERNAME,
                "items": [{"product_id": "PROD-001", "quantity": 2}],
                "total_amount": 99.99
            }
            
            response = requests.post(
                f"{ORDER_SERVICE}/orders",
                json=order_data,
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                order = response.json()
                self.log(f"✓ Order placed successfully", "SUCCESS")
                self.log(f"  Order ID: {order.get('order_id', 'N/A')}", "INFO")
                self.results.append(("order", "success", response.elapsed.total_seconds()))
                return True
            elif response.status_code == 503:
                self.log(f"✗ Order service unavailable (simulated fault)", "WARNING")
                self.results.append(("order", "unavailable", response.elapsed.total_seconds()))
                return False
            else:
                self.log(f"✗ Order failed: {response.status_code}", "ERROR")
                self.results.append(("order", "failed", response.elapsed.total_seconds()))
                return False
        
        except requests.exceptions.ConnectionError:
            self.log(f"✗ Order service not running yet (expected)", "WARNING")
            self.results.append(("order", "not_running", 0))
            return False
        except requests.exceptions.RequestException as e:
            self.log(f"✗ Order error: {e}", "ERROR")
            self.results.append(("order", "error", 0))
            return False
    
    def step_process_payment(self) -> bool:
        """Step 3: Process payment"""
        self.log("\n=== STEP 3: PROCESS PAYMENT ===")
        
        if not self.token:
            self.log("✗ No token available", "ERROR")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            payment_data = {
                "order_id": "ORDER-001",  # Would come from order service in real scenario
                "amount": 99.99,
                "payment_method": "credit_card"
            }
            
            response = requests.post(
                f"{PAYMENT_SERVICE}/payments",
                json=payment_data,
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                payment = response.json()
                self.log(f"✓ Payment processed successfully", "SUCCESS")
                self.log(f"  Payment ID: {payment.get('payment_id', 'N/A')}", "INFO")
                self.results.append(("payment", "success", response.elapsed.total_seconds()))
                return True
            else:
                self.log(f"✗ Payment failed: {response.status_code}", "ERROR")
                self.results.append(("payment", "failed", response.elapsed.total_seconds()))
                return False
        
        except requests.exceptions.ConnectionError:
            self.log(f"✗ Payment service not running yet (expected)", "WARNING")
            self.results.append(("payment", "not_running", 0))
            return False
        except requests.exceptions.RequestException as e:
            self.log(f"✗ Payment error: {e}", "ERROR")
            self.results.append(("payment", "error", 0))
            return False
    
    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "="*60, "INFO")
        self.log("TEST SUMMARY", "INFO")
        self.log("="*60, "INFO")
        
        for step, status, duration in self.results:
            duration_str = f"{duration:.3f}s" if duration > 0 else "N/A"
            print(f"  {step.upper():<15} {status.upper():<15} {duration_str}")
        
        print()
    
    def run_workflow(self, run_number: int = 1):
        """Run the complete workflow"""
        self.log(f"\n{'='*60}", "INFO")
        self.log(f"RUN #{run_number}", "INFO")
        self.log(f"{'='*60}", "INFO")
        
        # Step 1: Login (always required)
        if not self.step_login():
            self.log("Workflow aborted: login failed", "ERROR")
            return False
        
        # Step 2: Place order (will fail if service not running)
        self.step_place_order()
        
        # Step 3: Process payment (will fail if service not running)
        self.step_process_payment()
        
        self.print_summary()
        return True


def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test microservice workflow")
    parser.add_argument("--runs", type=int, default=1, help="Number of workflow runs (default: 1)")
    parser.add_argument("--delay", type=float, default=1, help="Delay between runs in seconds (default: 1)")
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("MICROSERVICE WORKFLOW TEST")
    print("="*60)
    print(f"Auth Service:    {AUTH_SERVICE}")
    print(f"Order Service:   {ORDER_SERVICE} (coming soon)")
    print(f"Payment Service: {PAYMENT_SERVICE} (coming soon)")
    print("="*60 + "\n")
    
    for run in range(1, args.runs + 1):
        runner = TestRunner()
        runner.run_workflow(run_number=run)
        
        if run < args.runs:
            print(f"\nWaiting {args.delay}s before next run...\n")
            time.sleep(args.delay)
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETE")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()