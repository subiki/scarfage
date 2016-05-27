$(document).ready(function(){
    $('ul.nav-pills a').click(function (e) {
        $(this).tab('show');
        var scrollmem = $('body').scrollTop();
        window.location.hash = this.hash;
        $('html,body').scrollTop(scrollmem);
    });

    $('div.tab-content div').click(function (e) {
        $(this).tab('show');
        var scrollmem = $('body').scrollTop();
        window.location.hash = this.hash;
        $('html,body').scrollTop(scrollmem);
    });

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

    // item button stuff. this should probably live in it's own file
    item_action('status');

    function item_action(action) {
       var itemid = $('#itemid').val();

       $.ajax({
          type: "POST",
          // all JS requests should be application/json even if not POST
          accepts: "application/json",
          url: '/item/' + itemid + '/' + action,
          success: function (itemstatus) {
              var obj = jQuery.parseJSON( itemstatus );
              update_buttons(obj);
          }
       });
    }

    function update_buttons(itemstatus) {
        $("#itemhavestatus").prop('value', itemstatus.have);
        if (itemstatus.have == '0') {
            $("#itemhiddenbutton").hide();
            $("#itemwilltradebutton").hide();
            $("#itemhavebutton").prop('value', 'Add to collection');
        } else {
            $("#itemhiddenbutton").show();
            $("#itemwilltradebutton").show();
            $("#itemhavebutton").prop('value', 'Remove from collection');
        }

        $("#itemhiddenstatus").prop('value', itemstatus.hidden);
        if (itemstatus.hidden == '0') {
            $("#itemhiddenbutton").prop('value', 'Hide item status from others');
        } else {
            $("#itemhiddenbutton").prop('value', 'Show item status to others');
        }

        $("#itemwilltradestatus").prop('value', itemstatus.willtrade);
        if (itemstatus.willtrade == '0') {
            $("#itemwilltradebutton").prop('value', 'Mark as available for trade');
        } else {
            $("#itemwilltradebutton").prop('value', 'Mark as unavailable for trade');
        }

        $("#itemwantstatus").prop('value', itemstatus.want);
        if (itemstatus.want == '0') {
            $("#itemwantbutton").prop('value', 'Add to want list');
        } else {
            $("#itemwantbutton").prop('value', 'Remove from want list');
        }
    }

    $('#itemhavebutton').click( function() {
       var status = $('#itemhavestatus').val();
       if (status == '0') {
           item_action('have'); 
       } else {
           item_action('donthave'); 
       }
    });

    $('#itemhiddenbutton').click( function() {
       var status = $('#itemhiddenstatus').val();
       if (status == '0') {
           item_action('hide'); 
       } else {
           item_action('show'); 
       }
    });

    $('#itemwilltradebutton').click( function() {
       var status = $('#itemwilltradestatus').val();
       if (status == '0') {
           item_action('willtrade'); 
       } else {
           item_action('wonttrade'); 
       }
    });

    $('#itemwantbutton').click( function() {
       var status = $('#itemwantstatus').val();
       if (status == '0') {
           item_action('want'); 
       } else {
           item_action('dontwant'); 
       }
    });
});
