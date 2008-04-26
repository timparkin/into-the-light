function click(id,suffix) {
  href = $(this).find('#'+id+' a'+suffix).attr('href');
  if (typeof(href) != 'undefined') {
    window.location=href;
  };
}

$.hotkeys.add('right', {propagate: true, disableInInput: true}, function(){ click('next','');  });
$.hotkeys.add('left', {propagate: true, disableInInput: true}, function(){ click('previous','');  });
$.hotkeys.add('up', {propagate: true, disableInInput: true}, function(){ click('up','');  });
$.hotkeys.add('down', {propagate: true, disableInInput: true}, function(){ click('photobody','.photo');  });

$.hotkeys.add('p', {propagate: true, disableInInput: true}, function(){ $(this).find('#price a').click(); });
$.hotkeys.add('i', {propagate: true, disableInInput: true}, function(){ $(this).find('#info a').click(); });

