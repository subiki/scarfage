$(document).ready(function(){
    function hideall(itemid) {
        $("#item-icons-have" + itemid).hide();
        $("#item-icons-donthave" + itemid).hide();
        $("#item-icons-show" + itemid).hide();
        $("#item-icons-hide" + itemid).hide();
        $("#item-icons-willtrade" + itemid).hide();
        $("#item-icons-wonttrade" + itemid).hide();
        $("#item-icons-want" + itemid).hide();
        $("#item-icons-dontwant" + itemid).hide();
    }

    $('div.itemiconsactionbox').each(function() {
        var itemid = $(this).attr('data-itemid');
        var dataid = $(this).attr('data-id');

        hideall(itemid);
        item_action(itemid, dataid, 'status', update_icons);
    });

    $('.item-icons-have').click( function() {
       var itemid = $(this).attr('data-itemid');
       var dataid = $(this).attr('data-id');
       item_action(itemid, dataid, 'have', update_icons); 
    });

    $('.item-icons-donthave').click( function() {
       var itemid = $(this).attr('data-itemid');
       var dataid = $(this).attr('data-id');
       item_action(itemid, dataid, 'donthave', update_icons); 
    });

    $('.item-icons-show').click( function() {
       var itemid = $(this).attr('data-itemid');
       var dataid = $(this).attr('data-id');
       item_action(itemid, dataid, 'show', update_icons); 
    });

    $('.item-icons-hide').click( function() {
       var itemid = $(this).attr('data-itemid');
       var dataid = $(this).attr('data-id');
       item_action(itemid, dataid, 'hide', update_icons); 
    });

    $('.item-icons-willtrade').click( function() {
       var itemid = $(this).attr('data-itemid');
       var dataid = $(this).attr('data-id');
       item_action(itemid, dataid, 'willtrade', update_icons); 
    });

    $('.item-icons-wonttrade').click( function() {
       var itemid = $(this).attr('data-itemid');
       var dataid = $(this).attr('data-id');
       item_action(itemid, dataid, 'wonttrade', update_icons); 
    });

    $('.item-icons-want').click( function() {
       var itemid = $(this).attr('data-itemid');
       var dataid = $(this).attr('data-id');
       item_action(itemid, dataid, 'want', update_icons); 
    });

    $('.item-icons-dontwant').click( function() {
       var itemid = $(this).attr('data-itemid');
       var dataid = $(this).attr('data-id');
       item_action(itemid, dataid, 'dontwant', update_icons); 
    });

    function update_icons(dataid, itemstatus) {
        if (itemstatus.have == '1') {
            $("#item-icons-have" + dataid).hide();
            $("#item-icons-donthave" + dataid).show();

            if (itemstatus.hidden == '0') {
                $("#item-icons-hide" + dataid).show();
                $("#item-icons-show" + dataid).hide();
            } else {
                $("#item-icons-hide" + dataid).hide();
                $("#item-icons-show" + dataid).show();
            }

            if (itemstatus.willtrade == '0') {
                $("#item-icons-willtrade" + dataid).show();
                $("#item-icons-wonttrade" + dataid).hide();
            } else {
                $("#item-icons-willtrade" + dataid).hide();
                $("#item-icons-wonttrade" + dataid).show();
            }
        } else {
            $("#item-icons-have" + dataid).show();
            $("#item-icons-donthave" + dataid).hide();
            $("#item-icons-hide" + dataid).hide();
            $("#item-icons-show" + dataid).hide();
            $("#item-icons-willtrade" + dataid).hide();
            $("#item-icons-wonttrade" + dataid).hide();
        }

        if (itemstatus.want == '0') {
            $("#item-icons-dontwant" + dataid).hide();
            $("#item-icons-want" + dataid).show();
        } else {
            $("#item-icons-dontwant" + dataid).show();
            $("#item-icons-want" + dataid).hide();
        }
    }

    function item_action(itemid, dataid, action, update) {
       if (itemid != null) {
           $.ajax({
              type: "POST",
              // all JS requests should be application/json even if not POST
              accepts: "application/json",
              url: '/item/' + itemid + '/' + action,
              success: function (itemstatus) {
                  var obj = jQuery.parseJSON( itemstatus );
                  update(dataid, obj);
              },
              error: function(XMLHttpRequest, textStatus, errorThrown) { 
                  alert("Status: " + textStatus); alert("Error: " + errorThrown); 
              }    
           });
       }
    }
});
