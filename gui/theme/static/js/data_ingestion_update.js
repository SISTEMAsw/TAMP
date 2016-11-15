$(document).ready(function() {
      $('input[name="access"]').click(function() {
       if($(this).attr('id') == 'id_access_0') {
            $('#dataInputFormGroup').hide();           
       }

       else {
            $('#dataInputFormGroup').show();   
       }
      });
    
    $('#updateBtn').attr("disabled",false);
 
   $('.cbox').change(function() {
      $('#updateBtn').attr('disabled', $('.cbox:checked').length == 0);
   });
   
   
    
    
});

