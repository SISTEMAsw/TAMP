$(document).ready(function() {

      $('.tool').tooltipster({
            animation: 'grow',
            delay: 100,
            trigger: 'hover',
            side: 'right',
      });
      var check = false;
      var check2 = false;

      /*$('#updateBtn').click(function() { 

            $.blockUI({ message: $('#uploadModal'),  css: { width: '275px' } }); 

            $.ajax({ 
                url: '/data-ingestion-page/', 
                cache: false, 
                success: function() { 
                    // unblock when remote call returns 
                    $.unblockUI(); 
                }
            }); 
        }); */

      $('input[name="access"]').click(function() {
       if($(this).prop('id') == 'id_access_1') {
            $('#dataInputFormGroup').show();           
       }

       else {
            $('#dataInputFormGroup').hide();   
       }
      });

      $('#updateBtn').prop("disabled",true);
    
   
   $('.cbox').change(function() {
      if (check == true)
      {
            $('#updateBtn').prop('disabled', $('.cbox:checked').length == 0);
            check2 = true;
      }
      else
      {
            $('#updateBtn').prop('disabled',true);
            check2 = false;
      }
   });  
        
   $('input[type=file]').change(function()
   {
      $("#name_question").fadeIn();
      $("#skip_1").show();
      $("#skip_3").hide();
      $("#skip_4").hide();
      $("#skip_5").hide();
   });
    
    $('#id_name').bind('keyup change',function(){
      if(this.value.length > 0)
      {
            check = true;
            if (check2 == true)
            {
                  $('#updateBtn').prop('disabled', $('.cbox:checked').length == 0);
            }
            else
            {
                  $('#updateBtn').prop('disabled',true);
                  $("#source_question").fadeIn();
                  $("#skip_1").hide();
                  $("#skip_3").show();
                  $("#skip_4").hide();
                  $("#skip_5").hide();                
            }
      }
      else
      {
            check = false;
            $('#updateBtn').prop('disabled',true);
      }
     
    });
    
    $('#id_source').bind('keyup change',function(){
      if(this.value.length > 0)
      {
            $("#geo_question").fadeIn();
            $("#skip_1").hide();
            $("#skip_3").hide();
            $("#skip_4").show();
            $("#skip_5").hide();    
      }
  
    });
    
    
      $('#skip_3').click(function(){
            $("#geo_question").fadeIn();
            $("#skip_3").hide();
            $("#skip_4").show();
            $("#skip_5").hide();
    });
    
      $('#skip_4').click(function(){

            $("#div_question").fadeIn();
            $("#skip_1").hide();
            $("#skip_3").hide();
            $("#skip_4").hide();
            $("#skip_5").show();

    });
      $('#skip_5').click(function(){
            $("#use_question").fadeIn();
            $("#skip_1").hide();
            $("#skip_3").hide();
            $("#skip_4").hide();
            $("#skip_5").hide();
    });
   
});

function validate(){
    if ($('#inputName').val().length   >   0   &&
       //$('input[type=file]').change() &&
       $('.cbox:checked').length != 0)
       {
             $('#updateBtn').prop("disabled", false);
    }
    else {
        $('#updateBtn').prop("disabled", true);
    }
}