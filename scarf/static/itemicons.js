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

        hideall(itemid);
        $("#item-icons-actionbox-hide" + itemid).hide();
    });

    $('div.itemiconsactionbox-nohide').each(function() {
        var itemid = $(this).attr('data-itemid');

        hideall(itemid);
        item_action(itemid, 'status', update_icons);
    });

    $('span.item-icons-actionbox-show').click(function() {
        var itemid = $(this).attr('data-itemid');

        $("#item-icons-actionbox-show" + itemid).hide();
        $("#item-icons-actionbox-hide" + itemid).show();

        item_action(itemid, 'status', update_icons);
    });

    $('span.item-icons-actionbox-hide').click(function() {
        var itemid = $(this).attr('data-itemid');

        hideall(itemid);
        $("#item-icons-actionbox-hide" + itemid).hide();
        $("#item-icons-actionbox-show" + itemid).show();
    });

    $('.item-icons-have').click( function() {
       var itemid = $(this).attr('data-itemid');
       item_action(itemid, 'have', update_icons); 
    });

    $('.item-icons-donthave').click( function() {
       var itemid = $(this).attr('data-itemid');
       item_action(itemid, 'donthave', update_icons); 
    });

    $('.item-icons-show').click( function() {
       var itemid = $(this).attr('data-itemid');
       item_action(itemid, 'show', update_icons); 
    });

    $('.item-icons-hide').click( function() {
       var itemid = $(this).attr('data-itemid');
       item_action(itemid, 'hide', update_icons); 
    });

    $('.item-icons-willtrade').click( function() {
       var itemid = $(this).attr('data-itemid');
       item_action(itemid, 'willtrade', update_icons); 
    });

    $('.item-icons-wonttrade').click( function() {
       var itemid = $(this).attr('data-itemid');
       item_action(itemid, 'wonttrade', update_icons); 
    });

    $('.item-icons-want').click( function() {
       var itemid = $(this).attr('data-itemid');
       item_action(itemid, 'want', update_icons); 
    });

    $('.item-icons-dontwant').click( function() {
       var itemid = $(this).attr('data-itemid');
       item_action(itemid, 'dontwant', update_icons); 
    });

    function update_icons(itemid, itemstatus) {
        if (itemstatus.have == '1') {
            $("#item-icons-have" + itemid).hide();
            $("#item-icons-donthave" + itemid).show();

            if (itemstatus.hidden == '0') {
                $("#item-icons-hide" + itemid).show();
                $("#item-icons-show" + itemid).hide();
            } else {
                $("#item-icons-hide" + itemid).hide();
                $("#item-icons-show" + itemid).show();
            }

            if (itemstatus.willtrade == '0') {
                $("#item-icons-willtrade" + itemid).show();
                $("#item-icons-wonttrade" + itemid).hide();
            } else {
                $("#item-icons-willtrade" + itemid).hide();
                $("#item-icons-wonttrade" + itemid).show();
            }
        } else {
            $("#item-icons-have" + itemid).show();
            $("#item-icons-donthave" + itemid).hide();
            $("#item-icons-hide" + itemid).hide();
            $("#item-icons-show" + itemid).hide();
            $("#item-icons-willtrade" + itemid).hide();
            $("#item-icons-wonttrade" + itemid).hide();
        }

        if (itemstatus.want == '0') {
            $("#item-icons-dontwant" + itemid).hide();
            $("#item-icons-want" + itemid).show();
        } else {
            $("#item-icons-dontwant" + itemid).show();
            $("#item-icons-want" + itemid).hide();
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
              },
              error: function(XMLHttpRequest, textStatus, errorThrown) { 
                  alert("Status: " + textStatus); alert("Error: " + errorThrown); 
              }    
           });
       }
    }
});
