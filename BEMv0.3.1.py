#%% md
# BEMv2.1
#%%
import os
import json
import sys
from pathlib import Path
from cryptography.fernet import Fernet
from getpass import getpass
#%%
class KEYVault:
    def __init__(self, usb_path: str, local_db_path: str = "passwords.json"):
        self.usb_path = Path(usb_path)
        self.keys_dir = self.usb_path / "vault_keys"
        self.local_db_path = Path(local_db_path)
        self.marker_file = self.usb_path / ".vault_active"


    def verify_key(self):
        if not self.usb_path.exists():
            raise FileNotFoundError(f"key drive not detected at '{self.usb_path}'. Please plug it in.")
        if not self.marker_file.exists():
            raise PermissionError("key drive detected, but vault marker is missing. Run setup first.")


    def setup_key(self):
        if not self.usb_path.exists():
            raise FileNotFoundError(f"Cannot find drive path '{self.usb_path}'.")
        self.keys_dir.mkdir(exist_ok=True)
        self.marker_file.touch(exist_ok=True)
        print(f"KEY Drive at '{self.usb_path}' initialized successfully!")


    def add_password(self, account_name: str, raw_password: str):
        self.verify_key()
        key = Fernet.generate_key()
        key_path = self.keys_dir / f"{account_name}.key"
        key_path.write_bytes(key)

        f = Fernet(key)
        encrypted_password = f.encrypt(raw_password.encode('utf-8')).decode('utf-8')

        db = self.load_db()
        db[account_name] = encrypted_password
        self.save_db(db)
        print(f"Password for '{account_name}' secured.")


    def update_password(self, account_name: str, new_password: str):
        self.verify_key()
        db = self.load_db()
        if account_name not in db:
            raise KeyError(f"Account '{account_name}' not found.")

        # generat a new key
        key = Fernet.generate_key()
        key_path = self.keys_dir / f"{account_name}.key"
        key_path.write_bytes(key)

        f = Fernet(key)
        enc_pass = f.encrypt(new_password.encode('utf-8')).decode('utf-8')

        db[account_name] = enc_pass
        self.save_db(db)
        print(f"Password for '{account_name}' has been updated.")


    def remove_password(self, account_name: str):
        self.verify_key()
        db = self.load_db()
        if account_name not in db:
            raise KeyError(f"Account '{account_name}' not found.")

        # Remove local encrypted password
        del db[account_name]
        self.save_db(db)

        # Remove key from USB
        key_path = self.keys_dir / f"{account_name}.key"
        if key_path.exists():
            key_path.unlink()

        print(f"Account '{account_name}' and its data have been ~Yeetus Deletus~.")


    def get_password(self, account_name: str) -> str:
        self.verify_key()
        db = self.load_db()
        if account_name not in db:
            raise KeyError(f"Account '{account_name}' not found.")

        encrypted_password = db[account_name].encode('utf-8')
        key_path = self.keys_dir / f"{account_name}.key"

        if not key_path.exists():
            raise FileNotFoundError(f"Key for '{account_name}' is missing from KEY drive!")

        key = key_path.read_bytes()
        f = Fernet(key)
        return f.decrypt(encrypted_password).decode('utf-8')


    def list_accounts(self):
        db = self.load_db()
        if not db:
            print("Bbbbut... its empty!")
            return
        print("\nStored accounts:")
        for account in sorted(db.keys()):
            print(f"  • {account}")


    def load_db(self) -> dict:
        if not self.local_db_path.exists():
            return {}
        try:
            return json.loads(self.local_db_path.read_text())
        except json.JSONDecodeError:
            return {}


    def save_db(self, db: dict):
        self.local_db_path.write_text(json.dumps(db, indent=4))


#%%
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')    #mac/linux/pc compatable?

#%% md
# config file
#%%
config_f= "BEM_config.json"

def load_config():
    if os.path.exists(config_f):
        try:
            with open(config_f, "r") as f:
                return json.load(f)
        except:
            return None
    return None

def save_config(usb_path, db_folder):
    try:
        with open(config_f, "w") as f:
            json.dump({"usb_path": usb_path, "db_folder": db_folder}, f, indent=4)
    except Exception as e:
        print(f"unable to save config: {e}")


#%% md
# UI
#%%
#art
vault_art = r"""
 _____________________________________________________
/                                                     \
|                   Baby Enigma Machine                |
|   /=====\            Passkey-Vault          /=====\  |
|  ((  O  ))       - ClearerVessel ind. -    ((  O  )) |
|   \=====/                                   \=====/  |
|======================================================|
|  ||  ||       _..-------------------.._       ||  || |
|  ||  ||     .'  _ _  _  _   _  _  _ _  '.     ||  || |
|  ||__||    /  .'  \| \/  \_/  \/ |/  '.  \    ||__|| |
|  [====]   |  |    _..-----------.._    |  |   [====] |
|  | () |   | |   .'  \  \  ||  /  /  '.   | |  | () | |
|  |    |   | |  /     \  \ || /  /     \  | |  |    | |
|  |==  |   | | |       \  \||/  /       | | |  |  ==| |
|  |  __|_  | | |  [O]   \==()_ /   [O]  | | |_ __  |  |
|  | |    | | | |========||(##)||========| | | |    |  |
|  | |____| | | |  [O]   /==()~ \   [O]  | | | |____|  |
|  |==    | | | |       /  /||\  \       | | | |   ==| |
|  |    |   | |  \     /  / || \  \     /  | |  |    | |
|  | () |   | |   '.  /__/__||__\__\  .'   | |  | () | |
|  [====]   |  |    `''-----------''`    |  |   [====] |
|  ||  ||    \  '.  /| /\  /^\  /\ |\  .'  /    ||  || |
|  ||  ||     '.  `''----------------''`  .'    ||  || |
|  ||__||       `''-------------------''`       ||__|| |
|======================================================|
|    |||                                         |||   |
|   _|||_               __   __                 _|||_  |
|  (_____)             (_ \ / _)               (_____) |
\_______________________ \_V_/ _______________________/
"""
#%% md
# pick location for KEY drive AND file
#%%
# menu
#maybe add some color later??
if __name__ == "__main__":
    clear_screen()
    print("========================================")
    print("         BABY ENIGMA MACHINE            ")
    print("========================================")

    config = load_config()
    use_saved = False
    db_folder_input = ""

    if config:
        print("Configuration loaded... ")
        print(f" • USB KEY PATH:   {config.get('usb_path')}")
        print(f" • Database folder: {config.get('db_folder') if config.get('db_folder') else 'Current Folder'}")
        print("\nWelcome back...")
        print("----------------------------------------")
        ans = input("Use previous Locations? \n1. Yes \n2. No \n Answer: ").strip().lower()
        if ans in ("1", "yes", "y", ""):
            use_saved = True
            usb_input = config.get("usb_path")
            db_folder_input = config.get("db_folder")

    if not use_saved:
        print("\n--- New Set Up ---")
        print("Examples for Key Path:")
        print("  Windows:  D:/  or  F:/")
        print("  macOS:    /Volumes/MyUSB")
        print("  Linux:    /media/username/MyUSB")
        print("----------------------------------------")
        usb_input = input("Enter the path to your USB drive: ").strip()

        if not usb_input:
            print("Path cannot be empty, You need a Key... Bye Now.")
            sys.exit(1)

        print("\n----------------------------------------")
        print("Database File Location (passwords.json):")
        print("  Press Enter to save in the current folder, or")
        print("  type a custom folder path (e.g., C:/Users/Name/Documents):")
        db_folder_input = input("Enter folder path: ").strip()

    # Process Database path
    if db_folder_input:
        db_dir = Path(db_folder_input)
        try:
            db_dir.mkdir(parents=True, exist_ok=True)
            db_path = db_dir / "passwords.json"
        except Exception as e:
            print(f"\nInvalid path or permission denied. Defaulting to current folder. Error: {e}")
            db_path = Path("passwords.json")
            input("\nPress Enter to continue . . .")
    else:
        db_path = Path("passwords.json")

    # Save the config file in the same location as the passwords database
    config_f = str(db_path.parent / "BEM_config.json")
    save_config(usb_input, db_folder_input)

    # Initialize key vault
    vault = KEYVault(usb_path=usb_input, local_db_path=db_path)

    while True:
        clear_screen()
        print(vault_art)
        print("========================================")
        print("1. Setup USB Drive")
        print("2. List all accounts")
        print("3. Add new password")
        print("4. Get password")
        print("5. Update password")
        print("6. Remove account")
        print("7. Exit")
        print()

        choice = input("Enter your choice (1-7): ").strip()

        try:
            if choice == "1":
                vault.setup_key()
            elif choice == "2":
                vault.list_accounts()
            elif choice == "3":
                account = input("Enter account name: ").strip()
                if account:
                    password = getpass(f"Enter password for '{account}': ")
                    confirm = getpass("Confirm password: ")
                    if password != confirm:
                        print("Passwords do not match!")
                    else:
                        vault.add_password(account, password)
                else:
                    print("Account name cannot be empty, No sneaky shit here buddy.")
            elif choice == "4":
                account = input("Enter account name: ").strip()
                if account:
                    password = vault.get_password(account)
                    print(f"\n🔑 Password for '{account}': {password}")
                else:
                    print("Account name cannot be empty, what do you expect me to look for?")
            elif choice == "5":
                account = input("Enter account name: ").strip()
                if account:
                    password = getpass(f"Enter NEW password for '{account}': ")
                    confirm = getpass("Confirm NEW password: ")
                    if password != confirm:
                        print("Passwords do not match, try again cant be that hard!")
                    else:
                        vault.update_password(account, password)
                else:
                    print("Account name cannot be empty.")
            elif choice == "6":
                account = input("Enter account to remove: ").strip()
                if account:
                    confirm = input(f"Delete '{account}'? This cannot be undone. Type 'DELETE' to confirm, or any button to cancel: ").strip()
                    if confirm == "DELETE":
                        vault.remove_password(account)
                    else:
                        print("Cancelled.")
                else:
                    print("Account name cannot be empty.")
            elif choice == "7":
                print("Goodbye!")
                break
            else:
                print("Numbers are hard, but I believe in you! Please choose a number from 1 to 7.")
        except Exception as e:
            print(f"Error: {e}")

        input("\nPress Enter to continue . . .")