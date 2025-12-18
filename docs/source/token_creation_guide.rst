Cloudflare Token Creation - Quick Reference
==============================================

🎯 What You Need: User API Token (NOT Account Token)
----------------------------------------------------

A **User API Token** can have both Account AND Zone permissions.
This is what the SaaS platform requires.

🔐 Three Ways to Create Token
-----------------------------

Method 1: Using Global API Key (Recommended - Most Reliable)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Get Your Global API Key:**

1. Go to: https://dash.cloudflare.com/profile/api-tokens
2. Scroll to "API Keys" section
3. Click "View" next to Global API Key (requires password)
4. Copy the key

**Create Token:**

.. code-block:: bash

   python create_token_with_global_key.py \
     --email your@email.com \
     --global-key your_global_api_key \
     --account-id 6451353ea5a8407bab6162abc42f5338 \
     --zone-id 2cf1f02313c4ef76af3d62eb78bb906e \
     --name "GETAIPAGE SaaS Token"

**Or set environment variables:**

.. code-block:: bash

   export CLOUDFLARE_EMAIL=your@email.com
   export CLOUDFLARE_GLOBAL_KEY=your_global_api_key
   export CLOUDFLARE_ACCOUNT_ID=6451353ea5a8407bab6162abc42f5338
   export CLOUDFLARE_ZONE_ID=2cf1f02313c4ef76af3d62eb78bb906e

   python create_token_with_global_key.py --name "GETAIPAGE SaaS Token"

Method 2: Using Existing Token with Creation Permission
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Requirements:**
- Existing token must have ``User:API Tokens:Edit`` permission

.. code-block:: bash

   python create_cloudflare_token.py \
     --account-id 6451353ea5a8407bab6162abc42f5338 \
     --zone-id 2cf1f02313c4ef76af3d62eb78bb906e \
     --name "GETAIPAGE Token"

Method 3: Manual Creation (Cloudflare Dashboard)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Recommended if scripts don't work:**

1. Go to: https://dash.cloudflare.com/profile/api-tokens
2. Create Token → Create Custom Token
3. Add permissions as listed in PERMISSIONS_GUIDE.md
4. Set resources and create

📋 Required Permissions Summary
--------------------------------

Account Permissions (All Accounts)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- ✅ Account Settings Read
- ✅ Workers R2 Storage Write
- ✅ Workers Scripts Read (for listing scripts)
- ✅ Workers Scripts Write (for deploying scripts)
- ✅ Workers Routes Write (for configuring routes)

Zone Permissions (Zone: ``2cf1f02313c4ef76af3d62eb78bb906e``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- ✅ Zone Read
- ✅ SSL and Certificates Read (for reading custom hostnames)
- ✅ SSL and Certificates Write (for managing custom hostnames)

🧪 After Creating Token
-----------------------

1. **Update .env:**

   .. code-block:: bash

      CLOUDFLARE_API_TOKEN=your_new_token_here

2. **Test permissions:**

   .. code-block:: bash

      python test_token_permissions.py
      # Should show 8/8 tests passed

3. **Deploy infrastructure:**

   .. code-block:: bash

      python examples/deploy_infrastructure.py

4. **Test deployment:**

   .. code-block:: bash

      python examples/full_deployment_example.py /path/to/site tenant domain.com

🔍 Available Helper Scripts
---------------------------

.. list-table:: Helper Scripts
   :header-rows: 1
   :widths: 30 40 30

   * - Script
     - Purpose
     - Requirements
   * - ``create_token_with_global_key.py``
     - Create token using Global API Key
     - Email + Global Key
   * - ``create_cloudflare_token.py``
     - Create token using existing token
     - Token with creation permission
   * - ``test_token_permissions.py``
     - Test current token permissions
     - Current API token
   * - ``add_missing_permissions.py``
     - Guide to add missing permissions
     - None (info only)
   * - ``manual_token_guide.py``
     - Manual creation guide
     - None (info only)

⚠️ Important Notes
------------------

1. **Global API Key vs API Token:**

   - Global Key: Full access, less secure (use only for creating tokens)
   - API Token: Scoped access, more secure (use for applications)

2. **Token Type:**

   - We need: **User API Token** (can have Account + Zone permissions)
   - NOT: Account Token (Account permissions only)
   - NOT: Zone Token (Zone permissions only)

3. **Security:**

   - Never commit tokens to version control
   - Use environment variables
   - Set token expiration when possible
   - Rotate tokens periodically

🆘 Troubleshooting
------------------

Script fails with authentication error
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Verify your Global API Key is correct
- Check email address matches Cloudflare account
- Ensure key hasn't been revoked

Token created but tests fail
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Token may have wrong permissions
- Delete and recreate with all required permissions
- Or edit existing token in dashboard to add missing permissions

Can't find Global API Key
^^^^^^^^^^^^^^^^^^^^^^^^^

- Go to: https://dash.cloudflare.com/profile/api-tokens
- Scroll to "API Keys" section (below API Tokens)
- Click "View" (requires password confirmation)