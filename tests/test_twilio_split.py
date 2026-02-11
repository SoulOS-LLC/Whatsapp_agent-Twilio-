
import sys
import os
import asyncio

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.twilio_service import TwilioService

def test_split_message():
    service = TwilioService()
    
    # Test 1: Short message (no split)
    short_msg = "This is a short message."
    chunks = service._split_message(short_msg, max_length=100)
    assert len(chunks) == 1
    assert chunks[0] == short_msg
    print("Test 1 Passed: Short message")
    
    # Test 2: Long message with spaces
    long_msg = "word " * 300  # 5 chars * 300 = 1500 chars
    # Limit to 100 chars
    chunks = service._split_message(long_msg, max_length=100)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 100
    print(f"Test 2 Passed: Long message split into {len(chunks)} chunks")
    
    # Test 3: Very long string with no spaces (hard split)
    hard_msg = "a" * 250
    chunks = service._split_message(hard_msg, max_length=100)
    assert len(chunks) == 3  # 100, 100, 50
    assert len(chunks[0]) == 100
    assert len(chunks[1]) == 100
    assert len(chunks[2]) == 50
    print("Test 3 Passed: Hard split")
    
    print("All tests passed!")

if __name__ == "__main__":
    test_split_message()
