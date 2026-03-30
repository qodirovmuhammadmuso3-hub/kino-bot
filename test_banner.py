import socket
import paramiko

host = "45.126.124.232"
port = 22

def check_banner():
    try:
        sock = socket.socket(socket.getaddrinfo(host, port)[0][0], socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        
        banner = sock.recv(1024)
        print(f"Banner: {banner}")
        sock.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_banner()
