var peEnabled = true;

$(document).ready(function(){
  v=$.cookie("peEnabled");
  if(v!=null) peEnabled=v=="true"?true:false;
  peEnabled=!peEnabled;
  peEnable();
  $('.pageelement a').click(function() {
    // intercept and disable content if ctrl key is pressed links. 
    if(peEnabled) {
      event = arguments[0];
      if(event && !event.ctrlKey)  return;
      $(this).parent().click();
      return false;
    }
  });

});

function peEnable() {
  peEnabled = peEnabled ? false:true;
  $.cookie("peEnabled", peEnabled, { path: '/' });
  if(peEnabled) {
    $('#peMenuEditOn').hide();
    $('#peMenuEditOff').show();
  } else {
    $('#peMenuEditOn').show();
    $('#peMenuEditOff').hide();
    //peHideAll();
  }
  $('.pageelement').each( function(index) {
    if(peEnabled)  $(this).hasClass("peBox") ? $(this).addClass("peBox_ov") : $(this).addClass("pageelement_ov");
    else           $(this).hasClass("peBox_ov") ? $(this).removeClass("peBox_ov") : $(this).removeClass("pageelement_ov");
    //alert(this.attr("class"));
  });
}

function peShowBlock(id) {
  //if(!peEnabled) return false;
  $('#'+id).show('slow');
}

function peHideBlock(id) {
  //if(!peEnabled) return false;
  $('#'+id).hide('slow');
}

function peLoadToggleBlock(url, id) {
  //if(!peEnabled) return false;
  ref = $('#'+id);
  if(ref.html()=="") { ref.load(url, function(){ ref.toggle('fast'); $.niveOverlay('#'+id);}); return; }
  ref.toggle('fast');
}

function peToggleBlock(id) {
  //if(!peEnabled) return false;
  $('#'+id).toggle('fast');
}

function peHideAll() {
  $('.pageeditorEditblockElement').each( function(index) {
    $(this).hide('fast');
  });
}

function peToggleMenu(id, event, hide) {
  $('#'+hide).hide('fast');
  $('#'+id).toggle('fast');
}

function peStopEvent(event) {
  if(!peEnabled) return false;
  if( event.stopPropagation ) { event.stopPropagation(); } 
  else { event.cancelBubble = true; } // IE
}

/* page element functions */

function peClickElement(id, event) {
  if(!peEnabled) return false;
  peStopEvent(event);
  peToggleBlock('edit'+id);
}

function peDblClickElement(id, event) {
  if(!peEnabled) return false;
  peStopEvent(event);
}


/**
* jQuery Cookie plugin
*
* Copyright (c) 2010 Klaus Hartl (stilbuero.de)
* Dual licensed under the MIT and GPL licenses:
* http://www.opensource.org/licenses/mit-license.php
* http://www.gnu.org/licenses/gpl.html
*
*/
jQuery.cookie = function (key, value, options) {

    // key and at least value given, set cookie...
    if (arguments.length > 1 && String(value) !== "[object Object]") {
        options = jQuery.extend({}, options);

        if (value === null || value === undefined) {
            options.expires = -1;
        }

        if (typeof options.expires === 'number') {
            var days = options.expires, t = options.expires = new Date();
            t.setDate(t.getDate() + days);
        }

        value = String(value);

        return (document.cookie = [
            encodeURIComponent(key), '=',
            options.raw ? value : encodeURIComponent(value),
            options.expires ? '; expires=' + options.expires.toUTCString() : '', // use expires attribute, max-age is not supported by IE
            options.path ? '; path=' + options.path : '',
            options.domain ? '; domain=' + options.domain : '',
            options.secure ? '; secure' : ''
        ].join(''));
    }

    // key and possibly options given, get cookie...
    options = value || {};
    var result, decode = options.raw ? function (s) { return s; } : decodeURIComponent;
    return (result = new RegExp('(?:^|; )' + encodeURIComponent(key) + '=([^;]*)').exec(document.cookie)) ? decode(result[1]) : null;
};

