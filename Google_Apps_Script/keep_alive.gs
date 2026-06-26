/**
 * Keeps Render services active by hitting their /keep-alive endpoints.
 * 
 * Instructions:
 * 1. Open Google Apps Script (script.google.com).
 * 2. Create a new project or open an existing one (e.g. SheetsFinance_Export).
 * 3. Add a new script file named 'keep_alive.gs' and paste this code.
 * 4. Replace the URLs with your actual Render service URLs.
 * 5. Set up a Time-driven trigger to run this function every 5 or 10 minutes.
 */
function keepRenderServicesAlive() {
  // URLs of the Render services to keep alive
  var urls = [
    "https://trading-automation-ingestor.onrender.com/keep-alive",   // Replace with actual ingestor URL
    "https://trading-automation-paper-trader.onrender.com/keep-alive" // Replace with actual paper trader URL
  ];
  
  urls.forEach(function(url) {
    try {
      var options = {
        "method": "get",
        "muteHttpExceptions": true,
        "headers": {
          "Cache-Control": "no-cache"
        }
      };
      
      var response = UrlFetchApp.fetch(url, options);
      var responseCode = response.getResponseCode();
      var content = response.getContentText();
      
      Logger.log("Hit URL: " + url);
      Logger.log("Response Code: " + responseCode);
      Logger.log("Response Content: " + content);
    } catch (e) {
      Logger.log("Error hitting URL: " + url + ". Error: " + e.toString());
    }
  });
}
