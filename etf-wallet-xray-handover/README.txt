YOUR ETF WALLET X-RAY: hand-over pack
======================================

Files
- etf-wallet-xray.html: the whole tool in one file (about 216 KB). Open it in a browser to run it. No build step.
- etf-wallet-xray-data-example.json: sample of every data format the tool accepts for live data.

Put it on a website
1. Upload etf-wallet-xray.html to the site (or embed it in an iframe).
2. The page loads d3, topojson and datamaps from cdnjs.cloudflare.com and cdn.jsdelivr.net, and fonts from Google Fonts. Allow those hosts if the site has a content security policy.
3. To connect live data, add this BEFORE the tool's script:

   <script>
   window.GCG_XRAY_CONFIG = {
     holdingsUrlTemplate: "/api/holdings/{t}.json",
     priceUrlTemplate: "/api/price/{t}.json",
     refreshMs: 60000,
     minWeight: 0.1,
     currency: "£"
   };
   </script>

4. Formats for the files above are in the developer spec and in the sample JSON. The comment block at the top of the tool's script lists every option.
5. In the browser console, GCGXRay.audit() lists funds with no price, fee or holdings.

Notes
- Portfolios are saved only in each visitor's own browser.
- Without a data feed the tool uses bundled snapshots and says so on screen. Performance and live price show empty states by design.
- Do not copy the code through Google Docs or word processors: they turn straight quotes into curly ones and break the code. Send the file itself.
