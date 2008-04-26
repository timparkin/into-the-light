





$(document).ready(function() {
  function alternateColors(parent, children, even, odd){
  $(parent).find(children + ':nth-child(even)').css('background-color', even);
  $(parent).find(children + ':nth-child(odd)').css('background-color', odd);
  };
  $('.categorieswidget .panel').hide();
  $('.categorieswidget .opener').click(function() {
    $(this).siblings('.panel').slideToggle();
    return false;
  });
  $('#search').hide();
  $('.search').click(function() {
    $('#search').slideToggle();
    return false;
  });  
  alternateColors($('table.tabular-view'), 'tr', '#FFFFFF', '#F8F8F8');
  
})


