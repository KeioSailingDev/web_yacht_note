jQuery( function($) {
    $('div[data-href]').addClass('clickable').click( function() {
        window.location = $(this).attr('data-href');
    }).find('a').hover( function() {
        $(this).parents('div').unbind('click');
    }, function() {
        $(this).parents('div').click( function() {
            window.location = $(this).attr('data-href');
        });
    });
});
