
# **Azure Files – Team Drive Mount Instructions (Windows & macOS)**

This document explains how to mount the shared Azure File Share for our project so you can drag and drop files just like a local folder.

## **📁 Storage Details**

- **Storage Account:** `smbclouddrive`
    
- **File Share Name:** `fs-a58a455239`
    
- **Credentials:**
    
    - **Username:** `AZURE\smbclouddrive`
        
    - **Password:** AlPX/0zAVPNXnRxCf7LdI4TYkfdxSN74Rzz0gMfn956+TBs6bliZW1xhL60JU5KiVvDrt+SJW+dZ+AStQ+hEZA==
        

## **🖥️ Windows Instructions**

### **1. Open Command Prompt or PowerShell**

### **2. Run the following command:**

Code

```
net use Z: \\smbclouddrive.file.core.windows.net\fs-a58a455239 /u:Azure\smbclouddrive AlPX/0zAVPNXnRxCf7LdI4TYkfdxSN74Rzz0gMfn956+TBs6bliZW1xhL60JU5KiVvDrt+SJW+dZ+AStQ+hEZA==
```

Replace:

- `<your-storage-account-key>` with the actual key
    
- `Z:` with any drive letter you prefer
    

### **3. After running the command**

A new drive (e.g., **Z:**) will appear in File Explorer. You can now:

- Drag & drop files
    
- Create folders
    
- Edit files directly
    

## **🍏 macOS Instructions**

### **1. Open Finder**

### **2. Press:**

**⌘ + K**

### **3. Enter this server address:**

Code

```
smb://smbclouddrive.file.core.windows.net/fs-a58a455239
```

### **4. When prompted for credentials**

- **Username:** `Azure\smbclouddrive`
    
- **Password:** `AlPX/0zAVPNXnRxCf7LdI4TYkfdxSN74Rzz0gMfn956+TBs6bliZW1xhL60JU5KiVvDrt+SJW+dZ+AStQ+hEZA==`
    

### **5. After connecting**

The share will mount like a network drive. You can drag & drop files normally.

## **🔐 Security Notes**

- This storage account is dedicated to the project.
    
- The shared key gives full access to this file share.
    
- The key will be rotated when the project ends.
