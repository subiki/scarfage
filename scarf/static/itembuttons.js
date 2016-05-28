$(document).ready(function(){
    // Load the status for the item
    $('div.itemactionbox').each(function() {
        var itemid = $(this).attr('data-itemid');
        item_action(itemid, 'status', update_buttons);
    });

    function button_toggle (obj, action_false, action_true) {
       var status = $(obj).attr('data-status') 
       var itemid = $(obj).parent().attr('data-itemid')
       $(obj).prop('value', 'Loading...');

       if (status == '0') {
           item_action(itemid, action_false, update_buttons); 
       } else {
           item_action(itemid, action_true, update_buttons); 
       }
    }

    $('input.itemhavebutton').click( function() {
       button_toggle(this, 'have', 'donthave');
    });

    $('input.itemhiddenbutton').click( function() {
       button_toggle(this, 'hide', 'show');
    });

    $('input.itemwilltradebutton').click( function() {
       button_toggle(this, 'willtrade', 'wonttrade');
    });

    $('input.itemwantbutton').click( function() {
       button_toggle(this, 'want', 'dontwant');
    });

    function update_buttons(itemid, itemstatus) {
        $('#itemhavebutton' + itemid).attr('data-status', itemstatus.have);
        if (itemstatus.have == '0') {
            $("#itemhiddenbutton" + itemid).hide();
            $("#itemwilltradebutton" + itemid).hide();
            $("#itemhavebutton" + itemid).prop('value', 'Add to collection');
        } else {
            $("#itemhiddenbutton" + itemid).show();
            $("#itemwilltradebutton" + itemid).show();
            $("#itemhavebutton" + itemid).prop('value', 'Remove from collection');
        }

        $("#itemhiddenbutton" + itemid).attr('data-status', itemstatus.hidden);
        if (itemstatus.hidden == '0') {
            $("#itemhiddenbutton" + itemid).prop('value', 'Hide item status from others');
        } else {
            $("#itemhiddenbutton" + itemid).prop('value', 'Show item status to others');
        }

        $("#itemwilltradebutton" + itemid).attr('data-status', itemstatus.willtrade);
        if (itemstatus.willtrade == '0') {
            $("#itemwilltradebutton" + itemid).prop('value', 'Mark as available for trade');
        } else {
            $("#itemwilltradebutton" + itemid).prop('value', 'Mark as unavailable for trade');
        }

        $("#itemwantbutton" + itemid).attr('data-status', itemstatus.want);
        if (itemstatus.want == '0') {
            $("#itemwantbutton" + itemid).prop('value', 'Add to want list');
        } else {
            $("#itemwantbutton" + itemid).prop('value', 'Remove from want list');
        }
    }

    function item_action(itemid, action, update) {
       if (itemid != null) {
           $.ajax({
              type: "POST",
              // all JS requests should be application/json even if not POST
              accepts: "application/json",
              url: '/item/' + itemid + '/' + action,
              success: function (itemstatus) {
                  var obj = jQuery.parseJSON( itemstatus );
                  update(itemid, obj);
              }
           });
       }
    }
});
