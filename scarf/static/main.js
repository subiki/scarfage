$(document).ready(function(){
    //Manage hash in URL to open the right pill
    var hash = window.location.hash;
    // If a hash is provided 
    if(hash && hash.length>0)
    {
        // Manage Pill titles
        $('ul.nav-pills li a').each(function( index ) {
            if($(this).attr('href')==hash)
                $(this).parent('li').addClass('active');
            else
                $(this).parent('li').removeClass('active');
        });

        // Manage Tab content
        var hash = hash.substring(1); // Remove the #
        $('div.tab-content div').each(function( index ) {
            if($(this).attr('id')==hash)
                $(this).addClass('fade in active');
            else
                $(this).removeClass('active');
        });
    }
});
