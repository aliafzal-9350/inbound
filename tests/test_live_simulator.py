import os
import sys
import time
import json
import httpx

def test_msg(msg):
    t0 = time.time()
    payload = {
        'system_prompt': 'You are a helpful sales assistant for RAVISN.',
        'message': msg
    }
    r = httpx.post('http://127.0.0.1:8000/settings/system-prompt/test', json=payload, timeout=60.0)
    dt = time.time() - t0
    data = r.json()
    msg_repr = json.dumps(msg, ensure_ascii=True)
    print(f'=== Message: {msg_repr} (Time: {dt:.3f}s, Status: {r.status_code}) ===')
    print('Reply:', json.dumps(data.get('reply'), ensure_ascii=True))
    print('Intent:', data.get('intent'))
    print('Language:', data.get('language'))
    print()



if __name__ == '__main__':
    print("Testing Live Simulator Fast-Path, Precision Brand Facts & Multi-Step Booking...")
    # 1. Greetings
    test_msg('hy')
    test_msg('AOA')
    test_msg('السلام علیکم')

    # 2. Critical Contact Facts
    test_msg('What is your email?')
    test_msg('What is your phone number?')
    test_msg('Where are you located?')
    test_msg('Aapka email kya hai?')
    test_msg('آپ کا ای میل کیا ہے؟')

    # 3. Industry & Packages
    test_msg('I have real estate business')
    test_msg('How much does it cost?')
    test_msg('What is in the All-in-One package?')

    # 4. Multi-Step Demo / Consultation Booking
    test_msg('I would like to book free demo')

