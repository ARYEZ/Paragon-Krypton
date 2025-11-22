# Force Kodi 17.6 Krypton to ONLY Use 1080p60 Interface

This configuration locks Kodi's interface to **1920x1080 @ 60Hz** by blacklisting all other available video modes.

## Installation Instructions

### Step 1: Copy advancedsettings.xml to Kodi userdata folder

On LibreELEC 8.2.5, you need to copy the `advancedsettings.xml` file to:

```
/storage/.kodi/userdata/
```

### Option A: Via SSH/SCP

1. **Enable SSH** on LibreELEC (if not already enabled):
   - Go to LibreELEC Settings → Services → Enable SSH

2. **Copy the file** using SCP from your computer:
   ```bash
   scp advancedsettings.xml root@YOUR_LIBREELEC_IP:/storage/.kodi/userdata/
   ```

3. **Or via SSH session**:
   ```bash
   ssh root@YOUR_LIBREELEC_IP
   # Then copy your advancedsettings.xml to /storage/.kodi/userdata/
   ```

### Option B: Via Samba/Network Share

1. **Enable Samba** in LibreELEC Settings → Services → Enable Samba
2. Navigate to `\\YOUR_LIBREELEC_IP\Userdata\` on your network
3. Copy `advancedsettings.xml` to this folder

### Option C: Direct Edit on Device

If you have direct access to the LibreELEC device:

```bash
nano /storage/.kodi/userdata/advancedsettings.xml
# Paste the contents and save
```

## Step 2: Set Initial Resolution

Before rebooting, ensure Kodi is set to 1080p60:

1. Go to **Settings → System Settings → Display**
2. Set **Resolution** to `1920x1080 @ 60Hz`
3. Confirm the change

## Step 3: Reboot Kodi

```bash
systemctl restart kodi
```

Or simply reboot LibreELEC:
```bash
reboot
```

## What This Does

The `advancedsettings.xml` file blacklists these 32 video modes:

- All refresh rates except 60Hz for 1920x1080
- All other resolutions (720p, 1024x768, 640x480, etc.)

**Only Available Mode:** `1920x1080 @ 60.000000 Hz` (ID: 0xe2)

This ensures:
- ✅ Kodi GUI stays at 1080p60 permanently
- ✅ No accidental resolution switching
- ✅ No refresh rate changes for the interface
- ✅ Consistent display output

## Verification

After reboot, check your Kodi log to confirm only 1080p60 is available:

```bash
cat /storage/.kodi/temp/kodi.log | grep "Available videomodes"
```

You should see only one available mode instead of 33.

## Troubleshooting

**If Kodi won't start or display is broken:**

1. SSH into LibreELEC
2. Remove the advancedsettings.xml:
   ```bash
   rm /storage/.kodi/userdata/advancedsettings.xml
   ```
3. Reboot

**Note:** This only affects the Kodi interface resolution. Video playback can still use different resolutions/refresh rates if you have "Adjust display refresh rate" enabled in playback settings.
