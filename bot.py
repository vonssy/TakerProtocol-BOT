from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout
)
from aiohttp_socks import ProxyConnector
from fake_useragent import FakeUserAgent
from eth_account.messages import encode_defunct
from eth_account import Account
from web3 import Web3
from colorama import *
from datetime import datetime
import asyncio, time, json, os, pytz

wib = pytz.timezone('Asia/Jakarta')

class TakerProtocol:
    def __init__(self) -> None:
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Host": "lightmining-api.taker.xyz",
            "Origin": "https://earn.taker.xyz",
            "Referer": "https://earn.taker.xyz/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": FakeUserAgent().random
        }
        self.ref_code = "RAGP0" # U can change it with yours.
        self.BASE_API = "https://lightmining-api.taker.xyz"
        self.RPC_URL = "https://rpc-mainnet.taker.xyz/"
        self.CONTRACT_ADDRESS = "0xB3eFE5105b835E5Dd9D206445Dbd66DF24b912AB"
        self.CONTRACT_ABI = [
            {
                "constant": False,
                "inputs": [],
                "name": "active",
                "outputs": [],
                "payable": False,
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def welcome(self):
        print(
            f"""
        {Fore.GREEN + Style.BRIGHT}Auto Claim {Fore.BLUE + Style.BRIGHT}Taker Lite Mining - BOT
            """
            f"""
        {Fore.GREEN + Style.BRIGHT}Rey? {Fore.YELLOW + Style.BRIGHT}<INI WATERMARK>
            """
        )

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    async def load_proxies(self, use_proxy_choice: int):
        filename = "proxy.txt"
        try:
            if use_proxy_choice == 1:
                async with ClientSession(timeout=ClientTimeout(total=30)) as session:
                    async with session.get("https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt") as response:
                        response.raise_for_status()
                        content = await response.text()
                        with open(filename, 'w') as f:
                            f.write(content)
                        self.proxies = content.splitlines()
            else:
                if not os.path.exists(filename):
                    self.log(f"{Fore.RED + Style.BRIGHT}File {filename} Not Found.{Style.RESET_ALL}")
                    return
                with open(filename, 'r') as f:
                    self.proxies = f.read().splitlines()
            
            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}No Proxies Found.{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Proxies Total  : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )
        
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed To Load Proxies: {e}{Style.RESET_ALL}")
            self.proxies = []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes):
            return proxies
        return f"http://{proxies}"

    def get_next_proxy_for_account(self, token):
        if token not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[token] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[token]

    def rotate_proxy_for_account(self, token):
        if not self.proxies:
            return None
        proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
        self.account_proxies[token] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy
    
    def generate_address(self, account: str):
        try:
            account = Account.from_key(account)
            address = account.address
            
            return address
        except Exception as e:
            return None
    
    def generate_payload(self, account: str, address: str, nonce: str):
        try:
            encoded_message = encode_defunct(text=nonce)
            signed_message = Account.sign_message(encoded_message, private_key=account)
            signature = signed_message.signature.hex()

            data = {
                "address":address, 
                "invitationCode":self.ref_code, 
                "message":nonce, 
                "signature":signature
            }
            
            return data
        except Exception as e:
            return None
        
    async def perform_onchain(self, account: str, address: str):
        web3 = Web3(Web3.HTTPProvider(self.RPC_URL))
        contract = web3.eth.contract(address=self.CONTRACT_ADDRESS, abi=self.CONTRACT_ABI)

        try:
            estimated_gas = contract.functions.active().estimate_gas({'from': address})
            gas_price = web3.eth.gas_price
            tx = contract.functions.active().build_transaction({
                'from': address,
                'nonce': web3.eth.get_transaction_count(address),
                'gas': estimated_gas,
                'gasPrice': gas_price
            })

            signed_tx = web3.eth.account.sign_transaction(tx, account)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

            return tx_hash.hex()
        except Exception as e:
            return None
    
    def mask_account(self, account):
        mask_account = account[:6] + '*' * 6 + account[-6:]
        return mask_account 
    
    def print_question(self):
        while True:
            try:
                print("1. Run With Monosans Proxy")
                print("2. Run With Private Proxy")
                print("3. Run Without Proxy")
                choose = int(input("Choose [1/2/3] -> ").strip())

                if choose in [1, 2, 3]:
                    proxy_type = (
                        "Run With Monosans Proxy" if choose == 1 else 
                        "Run With Private Proxy" if choose == 2 else 
                        "Run Without Proxy"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}{proxy_type} Selected.{Style.RESET_ALL}")
                    return choose
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter either 1, 2 or 3.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1, 2 or 3).{Style.RESET_ALL}")
        
    async def generate_nonce(self, address: str, proxy=None):
        url = f"{self.BASE_API}/wallet/generateNonce"
        data = json.dumps({"walletAddress":address})
        headers = {
            **self.headers,
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        connector = ProxyConnector.from_url(proxy) if proxy else None
        try:
            async with ClientSession(connector=connector, timeout=ClientTimeout(total=120)) as session:
                async with session.post(url=url, headers=headers, data=data) as response:
                    response.raise_for_status()
                    result = await response.json()
                    if "nonce" in result.get("data", None):
                        return result["data"]["nonce"]
                    return None
        except (Exception, ClientResponseError) as e:
            return None
    
    async def user_login(self, account: str, address: str, nonce: str, proxy=None, retries=5):
        url = f"{self.BASE_API}/wallet/login"
        data = json.dumps(self.generate_payload(account, address, nonce))
        headers = {
            **self.headers,
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=120)) as session:
                    async with session.post(url=url, headers=headers, data=data) as response:
                        response.raise_for_status()
                        result = await response.json()
                        return result["data"]["token"]
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue

                return None
    
    async def user_info(self, token: str, proxy=None, retries=5):
        url = f"{self.BASE_API}/user/getUserInfo"
        headers = {
            **self.headers,
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=120)) as session:
                    async with session.get(url=url, headers=headers) as response:
                        response.raise_for_status()
                        result = await response.json()
                        return result["data"]
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue

                return None
    
    async def mining_info(self, token: str, proxy=None, retries=5):
        url = f"{self.BASE_API}/assignment/totalMiningTime"
        headers = {
            **self.headers,
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=120)) as session:
                    async with session.get(url=url, headers=headers) as response:
                        response.raise_for_status()
                        result = await response.json()
                        return result["data"]
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue

                return None
    
    async def start_mining(self, token: str, status: bool, proxy=None, retries=5):
        url = f"{self.BASE_API}/assignment/startMining"
        data = json.dumps({"status":status})
        headers = {
            **self.headers,
            "Authorization": f"Bearer {token}",
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=120)) as session:
                    async with session.post(url=url, headers=headers, data=data) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue

                return None
            
    async def task_lists(self, token: str, proxy=None, retries=5):
        url = f"{self.BASE_API}/assignment/list"
        headers = {
            **self.headers,
            "Authorization": f"Bearer {token}",
            "Content-Length": "0",
            "Content-Type": "application/json"
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=120)) as session:
                    async with session.post(url=url, headers=headers) as response:
                        response.raise_for_status()
                        result = await response.json()
                        return result["data"]
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue

                return None
    
    async def complete_tasks(self, token: str, task_id: int, proxy=None, retries=5):
        url = f"{self.BASE_API}/assignment/do"
        data = json.dumps({"assignmentId":task_id})
        headers = {
            **self.headers,
            "Authorization": f"Bearer {token}",
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=120)) as session:
                    async with session.post(url=url, headers=headers, data=data) as response:
                        response.raise_for_status()
                        result = await response.json()
                        return result["data"]
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue

                return None
            
    async def process_accounts(self, account: str, address: str, use_proxy: bool):
        proxy = self.get_next_proxy_for_account(address) if use_proxy else None
        nonce = None
        while nonce is None:
            nonce = await self.generate_nonce(address, proxy)
            if not nonce:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Status    :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} GET Nonce Failed {Style.RESET_ALL}"
                )

                proxy = self.rotate_proxy_for_account(address) if use_proxy else None
                await asyncio.sleep(3)
                continue

            token = await self.user_login(account, address, nonce, proxy)
            if not token:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Status    :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Login Failed {Style.RESET_ALL}"
                )
                return
            
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Status    :{Style.RESET_ALL}"
                f"{Fore.GREEN+Style.BRIGHT} Login Success {Style.RESET_ALL}"
            )

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Proxy     :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {proxy} {Style.RESET_ALL}"
            )
            
            balance = 0
            tw_id = None

            user = await self.user_info(token, proxy)
            if user:
                balance = f"{float(user.get('totalReward', 0)):.1f}"
                tw_id = user.get('twId', None)

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Balance   :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {balance} Opoints {Style.RESET_ALL}"
            )

            if tw_id is None:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Mining    :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Not Eligible {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Connect Ur Social Media First {Style.RESET_ALL}"
                )
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Task Lists:{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Not Eligible {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Connect Ur Social Media First {Style.RESET_ALL}"
                )
                return
            
            mining = await self.mining_info(token, proxy)
            if mining:
                last_mining = mining.get('lastMiningTime', 0)

                if last_mining == 0:
                    start = await self.start_mining(token, True, proxy)
                    if start and start.get("data") == "ok":
                        self.log(
                            f"{Fore.CYAN+Style.BRIGHT}Mining    :{Style.RESET_ALL}"
                            f"{Fore.GREEN+Style.BRIGHT} Is Started {Style.RESET_ALL}"
                        )
                    else:
                        self.log(
                            f"{Fore.CYAN+Style.BRIGHT}Mining    :{Style.RESET_ALL}"
                            f"{Fore.RED+Style.BRIGHT} Isn't Started {Style.RESET_ALL}"
                        )
                else:
                    timestamp = int(time.time())
                    reactive_time = last_mining + 86400

                    if timestamp >= reactive_time:
                        tx_hash = await self.perform_onchain(account, address)
                        if tx_hash:
                            start = await self.start_mining(token, False, proxy)
                            if start and start.get("data") == "ok":
                                self.log(
                                    f"{Fore.CYAN+Style.BRIGHT}Mining    :{Style.RESET_ALL}"
                                    f"{Fore.GREEN+Style.BRIGHT} Is Activated {Style.RESET_ALL}"
                                )
                                self.log(
                                    f"{Fore.CYAN+Style.BRIGHT}      >{Style.RESET_ALL}"
                                    f"{Fore.WHITE+Style.BRIGHT} Tx Hash: {Style.RESET_ALL}"
                                    f"{Fore.BLUE+Style.BRIGHT}{self.mask_account(tx_hash)}{Style.RESET_ALL}"
                                )
                            else:
                                self.log(
                                    f"{Fore.CYAN+Style.BRIGHT}Mining    :{Style.RESET_ALL}"
                                    f"{Fore.RED+Style.BRIGHT} Isn't Activated {Style.RESET_ALL}"
                                )
                        else:
                            self.log(
                                f"{Fore.CYAN+Style.BRIGHT}Mining    :{Style.RESET_ALL}"
                                f"{Fore.RED+Style.BRIGHT} Isn't Activated {Style.RESET_ALL}"
                                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                                f"{Fore.YELLOW+Style.BRIGHT} OnChain Tx Failed {Style.RESET_ALL}"
                            )
                    else:
                        test = datetime.fromtimestamp(reactive_time).astimezone(wib).strftime('%x %X %Z')
                        self.log(
                            f"{Fore.CYAN+Style.BRIGHT}Mining    :{Style.RESET_ALL}"
                            f"{Fore.YELLOW+Style.BRIGHT} Is Already Activated {Style.RESET_ALL}"
                            f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                            f"{Fore.CYAN+Style.BRIGHT} Next Activate at {Style.RESET_ALL}"
                            f"{Fore.WHITE+Style.BRIGHT}{test}{Style.RESET_ALL}"
                        )

            else:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Mining    :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Data Is None {Style.RESET_ALL}"
                )

            tasks = await self.task_lists(token, proxy)
            if tasks:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Task Lists:{Style.RESET_ALL}"
                    f"{Fore.GREEN+Style.BRIGHT} Available {Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT}{len(tasks)} Tasks{Style.RESET_ALL}"
                )

                for task in tasks:
                    if task:
                        task_id = task["assignmentId"]
                        title = task['title']
                        reward = task['reward']
                        is_done = task["done"]

                        if is_done:
                            self.log(
                                f"{Fore.CYAN+Style.BRIGHT}      > {Style.RESET_ALL}"
                                f"{Fore.WHITE+Style.BRIGHT}{title}{Style.RESET_ALL}"
                                f"{Fore.YELLOW+Style.BRIGHT} Is Already Completed {Style.RESET_ALL}"
                            )
                            continue

                        complete = await self.complete_tasks(token, task_id, proxy)
                        if complete:
                            self.log(
                                f"{Fore.CYAN+Style.BRIGHT}      > {Style.RESET_ALL}"
                                f"{Fore.WHITE+Style.BRIGHT}{title}{Style.RESET_ALL}"
                                f"{Fore.GREEN+Style.BRIGHT} Is Completed {Style.RESET_ALL}"
                                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                                f"{Fore.CYAN+Style.BRIGHT} Reward {Style.RESET_ALL}"
                                f"{Fore.WHITE+Style.BRIGHT}{reward} Opoints{Style.RESET_ALL}"
                            )
                        else:
                            self.log(
                                f"{Fore.CYAN+Style.BRIGHT}      > {Style.RESET_ALL}"
                                f"{Fore.WHITE+Style.BRIGHT}{title}{Style.RESET_ALL}"
                                f"{Fore.RED+Style.BRIGHT} Not Completed {Style.RESET_ALL}"
                            )
                        await asyncio.sleep(1)

            else:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Task Lists:{Style.RESET_ALL}"
                    f"{Fore.GREEN+Style.BRIGHT} Data Is None {Style.RESET_ALL}"
                )

    async def main(self):
        try:
            with open('accounts.txt', 'r') as file:
                accounts = [line.strip() for line in file if line.strip()]
            
            use_proxy_choice = self.print_question()

            while True:
                use_proxy = False
                if use_proxy_choice in [1, 2]:
                    use_proxy = True

                self.clear_terminal()
                self.welcome()
                self.log(
                    f"{Fore.GREEN + Style.BRIGHT}Account's Total: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}"
                )

                if use_proxy:
                    await self.load_proxies(use_proxy_choice)
                
                separator = "=" * 25
                for account in accounts:
                    if account:
                        address = self.generate_address(account)
                        self.log(
                            f"{Fore.CYAN + Style.BRIGHT}{separator}[{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} {self.mask_account(address)} {Style.RESET_ALL}"
                            f"{Fore.CYAN + Style.BRIGHT}]{separator}{Style.RESET_ALL}"
                        )
                        await self.process_accounts(account, address, use_proxy)
                        await asyncio.sleep(3)

                self.log(f"{Fore.CYAN + Style.BRIGHT}={Style.RESET_ALL}"*72)
                seconds = 12 * 60 * 60
                while seconds > 0:
                    formatted_time = self.format_seconds(seconds)
                    print(
                        f"{Fore.CYAN+Style.BRIGHT}[ Wait for{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {formatted_time} {Style.RESET_ALL}"
                        f"{Fore.CYAN+Style.BRIGHT}... ]{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE+Style.BRIGHT}All Accounts Have Been Processed.{Style.RESET_ALL}",
                        end="\r"
                    )
                    await asyncio.sleep(1)
                    seconds -= 1

        except FileNotFoundError:
            self.log(f"{Fore.RED}File 'accounts.txt' Not Found.{Style.RESET_ALL}")
            return
        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Error: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        bot = TakerProtocol()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.RED + Style.BRIGHT}[ EXIT ] Taker Lite Mining - BOT{Style.RESET_ALL}                                       "                              
        )