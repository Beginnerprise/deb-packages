var callAPI = "http://phones1.bp.local/cgi-bin/call.cgi";
var phonelistAPI = "http://intranet1.bp.local/cgi-bin/phonelist.cgi";

function main() {

  $('#submit_extension').click(function(event) {
    setCookie("extension",$('#extension').val());
    if ($('#extension').val())
    {
      $('#enter_extension').slideUp('slow');
      alert('Now you can click an extension to dial');
    }
  });

  $('#enter_extension').hide();

  if (getCookie('extension'))
  {
    $('#extension').val(getCookie('extension'));
  }

  var requestData = "";
  requestData += "&command=getphones";
  getAjaxResponse(phonelistAPI,requestData,doHandlePopulateTableResults);

  return false;

}

function setCookie(key,value) {
  var tmpcookie = "";
  var days = "365";

  var date = new Date();
  date.setTime(date.getTime()+(days*24*60*60*1000));
  var expires = "; expires="+date.toGMTString();

  tmpcookie += key + "=" + value + expires +"; path=/";
  document.cookie = key + '=; expires=Thu, 01 Jan 1970 00:00:01 GMT;';
  if (value != "")
  {
    document.cookie = tmpcookie;
  }
}

function doHandleCallResults(results) {
  if (results["error"]) {
    alert('Error: ' + results["error"]["message"]);
  }
  if (results["response"]) {
    // Respond Positive
  }
}

function doHandlePopulateTableResults(results) {

  var table = "";
  for (var phone in results)
  {
    table += "<tr>";
    table += "  <td>" + results[phone]["firstname"] + "</td>";
    table += "  <td>" + results[phone]["lastname"] + "</td>";
    table += "  <td>" + results[phone]["company"] + "</td>";
    table += "  <td><a href=><span class=\"phone_click\">" + results[phone]["extension"] + "</span></a></td>";
    table += "  <td><a href=mailto:" + results[phone]["email"] + ">" + results[phone]["email"]  +"</td>";
    table += "  <td>" + results[phone]["mac"] + "</td>";
    table += "</tr>";
  }

  $('#phonetable').html(table);

  $('#phones').dataTable( {
    "bPaginate": false
  });

  $(".phone_click").click(function(event) {

    if ($('#extension').val())
    {
      var number_to_dial = $(this).text();
      var source_extension = $('#extension').val();
      var requestData = "";

      requestData += "&number_to_dial=" + number_to_dial;
      requestData += "&source_extension=" + source_extension;
      requestData += "&command=dial";

      getAjaxResponse(callAPI,requestData,doHandleCallResults);
      return false;
    }
    else
    {
      $("html,body").animate({ scrollTop: 0 }, "slow");
      $('#enter_extension').slideDown('slow');
    }

    return false; // Make HREFS not actually click
  });

}

function getAjaxResponse(server,requestData,handler) {

  if (request) {
    request.abort();
  }

  requestData += "&responsetype=json";

  var request = $.ajax({
    url : server,
    type : "post",
    data : requestData
  });

  request.done(function(response, textStatus, jqXHR) {
    handler(response);
  });

  request.fail(function(jqXHR, textStatus, error) {
    console.error("Error: " + textStatus, error);
  });

  request.always(function() {
    // Stuff to always run
  });
}

if (typeof String.prototype.trimLeft !== "function") {
  String.prototype.trimLeft = function() {
    return this.replace(/^\s+/, "");
  };
}
if (typeof String.prototype.trimRight !== "function") {
  String.prototype.trimRight = function() {
    return this.replace(/\s+$/, "");
  };
}
if (typeof Array.prototype.map !== "function") {
  Array.prototype.map = function(callback, thisArg) {
    for (var i=0, n=this.length, a=[]; i<n; i++) {
      if (i in this) a[i] = callback.call(thisArg, this[i]);
    }
    return a;
  };
}

function getCookies() {
  var c = document.cookie, v = 0, cookies = {};
  if (document.cookie.match(/^\s*\$Version=(?:"1"|1);\s*(.*)/)) {
    c = RegExp.$1;
    v = 1;
  }
  if (v === 0) {
    c.split(/[,;]/).map(function(cookie) {
      var parts = cookie.split(/=/, 2),
      name = decodeURIComponent(parts[0].trimLeft()),
      value = parts.length > 1 ? decodeURIComponent(parts[1].trimRight()) : null;
      cookies[name] = value;
    });
  } else {
    c.match(/(?:^|\s+)([!#$%&'*+\-.0-9A-Z^`a-z|~]+)=([!#$%&'*+\-.0-9A-Z^`a-z|~]*|"(?:[\x20-\x7E\x80\xFF]|\\[\x00-\x7F])*")(?=\s*[,;]|$)/g).map(function($0, $1) {
      var name = $0,
      value = $1.charAt(0) === '"'
      ? $1.substr(1, -1).replace(/\\(.)/g, "$1")
      : $1;
      cookies[name] = value;
    });
  }
  return cookies;
}

function getCookie(name) {
  return getCookies()[name];
}



$(window).load(function() {
  main();
});
