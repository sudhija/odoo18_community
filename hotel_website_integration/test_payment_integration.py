#!/usr/bin/env python3
"""
Test script for Hotel Payment Integration
Run this to verify your payment setup is working correctly.
"""

def test_payment_integration():
    """
    Test steps for hotel payment integration:
    
    1. Enable Demo Payment Provider:
       - Go to Website → Configuration → Payment Providers
       - Find "Demo Provider" → Edit → Set State to "Enabled"
       - Make sure it's assigned to your website
       - Save
    
    2. Test URLs:
       - Debug: http://your-domain/hotel/debug/payment
       - Hotel: http://your-domain/hotel
       - Providers: http://your-domain/hotel/payment/providers
    
    3. Test Booking Flow:
       - Go to /hotel
       - Select dates and book a room
       - Fill form and submit
       - Should redirect to payment (not /shop/checkout)
    
    4. Expected Behavior:
       - If Demo provider enabled → redirects to /payment/process/<tx_id>
       - If no providers → redirects to /hotel/payment/providers
       - Never falls back to /shop/checkout
    """
    
    print("🔧 Hotel Payment Integration Test")
    print("=" * 50)
    
    print("\n1. Enable Demo Payment Provider:")
    print("   - Website → Configuration → Payment Providers")
    print("   - Demo Provider → Edit → State: Enabled")
    print("   - Assign to your website")
    
    print("\n2. Test URLs:")
    print("   - Debug: /hotel/debug/payment")
    print("   - Hotel: /hotel")
    print("   - Providers: /hotel/payment/providers")
    
    print("\n3. Expected Flow:")
    print("   - Book room → Create transaction → Redirect to payment")
    print("   - Demo provider → /payment/process/<tx_id>")
    print("   - No providers → /hotel/payment/providers")
    print("   - Never → /shop/checkout")
    
    print("\n4. Debug Commands:")
    print("   - Check logs for: 'Created draft booking' and 'Redirecting to payment'")
    print("   - Check browser console for payment form submission")
    
    print("\n✅ If you see /payment/process/<tx_id>, payment integration is working!")
    print("❌ If you see /shop/checkout, check provider configuration")

if __name__ == "__main__":
    test_payment_integration()



