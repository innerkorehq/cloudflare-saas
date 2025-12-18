DNS Configuration Guide for getai.page
========================================

Good News!
----------

Your zone is **active** and the **worker route is already configured**! You just need to add one DNS record.

Quick Setup (2 minutes)
-----------------------

Add Wildcard DNS Record
^^^^^^^^^^^^^^^^^^^^^^^

1. **Go to Cloudflare Dashboard:**

   .. code-block:: text

      https://dash.cloudflare.com/2cf1f02313c4ef76af3d62eb78bb906e/getai.page/dns/records

2. **Click "Add record"**

3. **Enter these values:**

   - **Type:** ``AAAA``
   - **Name:** ``*`` (just an asterisk)
   - **IPv6 address:** ``100::``
   - **Proxy status:** ✅ ON (Orange cloud enabled)
   - **TTL:** Auto

4. **Click "Save"**

That's it! 🎉

What This Does
--------------

The wildcard record (``*.getai.page``) will route **all** tenant subdomains to Cloudflare's network:

- ``tenant-finaldemo.getai.page`` ✅
- ``tenant-testdemo.getai.page`` ✅
- ``tenant-mycompany.getai.page`` ✅
- Any ``tenant-*.getai.page`` subdomain ✅

Already Configured
------------------

✅ **Zone Status:** Active
✅ **Name Servers:** betty.ns.cloudflare.com, kevin.ns.cloudflare.com
✅ **Worker Route:** ``*.getai.page/*`` → ``getaipage-router``
✅ **Worker Script:** Deployed with R2 binding

After Adding DNS Record
-----------------------

Wait 1-2 minutes for DNS propagation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Then test your deployed tenants:

.. code-block:: bash

   # Test health endpoint
   curl https://tenant-finaldemo.getai.page/_health

   # Test actual site
   curl -I https://tenant-finaldemo.getai.page/

Verify DNS Resolution
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Check if wildcard DNS is working
   dig tenant-finaldemo.getai.page

   # Should show Cloudflare IPs (proxied)
   # Look for ANSWER SECTION with Cloudflare addresses

Or use online checker:

- https://dnschecker.org/#tenant-finaldemo.getai.page

Your Deployed Tenants
---------------------

These will be accessible once DNS record is added:

.. list-table:: Deployed Tenants
   :header-rows: 1
   :widths: 30 70

   * - Tenant
     - URL
   * - tenant-finaldemo
     - https://tenant-finaldemo.getai.page/
   * - tenant-testdemo
     - https://tenant-testdemo.getai.page/
   * - tenant-getaipage2
     - https://tenant-getaipage2.getai.page/
   * - tenant-getaipage
     - https://tenant-getaipage.getai.page/

Troubleshooting
---------------

If you get "This site can't be reached" error
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. **Check DNS record exists:**

   - Go to DNS settings in Cloudflare
   - Confirm ``* → 100::`` record exists
   - Confirm proxy (orange cloud) is ON

2. **Wait for propagation:**

   - DNS changes can take 1-5 minutes
   - Sometimes up to 30 minutes globally

3. **Check worker logs:**

   - https://dash.cloudflare.com/6451353ea5a8407bab6162abc42f5338/workers/services/view/getaipage-router
   - Look for any errors

If you get 404 or 500 errors
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. **Verify files are in R2:**

   .. code-block:: bash

      # List files for a tenant
      python -c "
      import boto3, os
      s3 = boto3.client('s3',
          endpoint_url=os.getenv('R2_ENDPOINT'),
          aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
          aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
          region_name='auto')

      objs = s3.list_objects_v2(Bucket='getaipage', Prefix='tenant-finaldemo/')
      for obj in objs.get('Contents', [])[:10]:
          print(obj['Key'])
      "

2. **Check worker is deployed:**

   .. code-block:: bash

      python deploy_worker.py

Alternative: Use A Record Instead of AAAA
------------------------------------------

If you prefer IPv4:

- **Type:** ``A``
- **Name:** ``*``
- **IPv4 address:** ``192.0.2.1`` (placeholder for proxied)
- **Proxy:** ✅ ON

(When proxied, Cloudflare handles the actual IP routing)

Manual DNS Configuration Complete Checklist
-------------------------------------------

- [ ] Open Cloudflare Dashboard → DNS
- [ ] Add AAAA record: ``* → 100::``
- [ ] Enable proxy (orange cloud)
- [ ] Save record
- [ ] Wait 2 minutes
- [ ] Test: ``curl https://tenant-finaldemo.getai.page/_health``
- [ ] Should return: ``OK``

Need More Help?
---------------

The script ``configure_dns.py`` attempted to add this automatically but needs DNS edit permissions. You can:

1. **Add the permission to your API token:**

   - Go to API Tokens in Cloudflare
   - Edit token: ``2MfCcf2yvvTUjzNtfVcD-UIy6bf6t_wnPcSc9MqV``
   - Add permission: **Zone / DNS / Edit**
   - Then run: ``python configure_dns.py``

2. **Or just add it manually (faster!):** Follow the steps above

Status: One DNS record away from being fully operational! 🚀