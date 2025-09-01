"""
Server Module for Network Communication

This module contains the socket server for receiving data from sensor nodes.
"""

import socket
import threading
import logging
import json

# Configure logging
logger = logging.getLogger(__name__)

class DataServer:
    """Socket server for receiving data from sensor nodes."""
    
    def __init__(self, config, data_handler):
        """
        Initialize the data server with the given configuration.
        
        Args:
            config (dict): Configuration dictionary
            data_handler (callable): Function to handle received data
        """
        self.config = config
        self.data_handler = data_handler
        self.server_socket = None
        self.running = False
        self.thread = None
    
    def start(self):
        """Start the data server."""
        if self.running:
            logger.warning("Server is already running")
            return
        
        try:
            # Create socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to port
            self.server_socket.bind(('0.0.0.0', self.config["listen_port"]))
            
            # Listen for connections
            self.server_socket.listen(5)
            
            # Set running flag
            self.running = True
            
            # Start server thread
            self.thread = threading.Thread(target=self._run_server)
            self.thread.daemon = True
            self.thread.start()
            
            logger.info(f"Data server started on port {self.config['listen_port']}")
            return True
        except Exception as e:
            logger.error(f"Error starting data server: {e}")
            if self.server_socket:
                self.server_socket.close()
            return False
    
    def _run_server(self):
        """Run the server loop."""
        logger.info("Server loop started")
        
        while self.running:
            try:
                # Accept connection
                client_socket, addr = self.server_socket.accept()
                logger.info(f"Connection from {addr[0]}:{addr[1]}")
                
                # Handle client in a new thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, addr)
                )
                client_thread.daemon = True
                client_thread.start()
            except Exception as e:
                if self.running:  # Only log if we're still supposed to be running
                    logger.error(f"Error accepting connection: {e}")
        
        logger.info("Server loop stopped")
    
    def _handle_client(self, client_socket, addr):
        """
        Handle a client connection.
        
        Args:
            client_socket (socket.socket): The client socket
            addr (tuple): The client address (ip, port)
        """
        try:
            # Set a timeout for receiving data
            client_socket.settimeout(5)
            
            # Receive data
            data = b""
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                data += chunk
                
                # Check if we have a complete JSON object
                try:
                    # Try to decode and parse the data
                    json_data = json.loads(data.decode('utf-8'))
                    
                    # Handle the data
                    result = self.data_handler(json_data, addr)
                    
                    # Send response
                    if result:
                        client_socket.sendall(b'{"status": "success"}')
                    else:
                        client_socket.sendall(b'{"status": "error", "message": "Failed to process data"}')
                    
                    break
                except json.JSONDecodeError:
                    # Not a complete JSON object yet, continue receiving
                    continue
        except socket.timeout:
            logger.warning(f"Connection from {addr[0]}:{addr[1]} timed out")
            client_socket.sendall(b'{"status": "error", "message": "Connection timed out"}')
        except Exception as e:
            logger.error(f"Error handling client {addr[0]}:{addr[1]}: {e}")
            try:
                client_socket.sendall(b'{"status": "error", "message": "Internal server error"}')
            except:
                pass
        finally:
            # Close the connection
            client_socket.close()
    
    def stop(self):
        """Stop the data server."""
        if not self.running:
            logger.warning("Server is not running")
            return
        
        try:
            # Set running flag to False
            self.running = False
            
            # Close the socket
            if self.server_socket:
                self.server_socket.close()
            
            # Wait for thread to finish
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=5)
            
            logger.info("Data server stopped")
            return True
        except Exception as e:
            logger.error(f"Error stopping data server: {e}")
            return False