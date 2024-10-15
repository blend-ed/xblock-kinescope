function KinescopeStudioXBlock(runtime, element) {

    var handlerUrl = runtime.handlerUrl(element, 'studio_submit');

    $(element).find('.save-button').bind('click', function() {
        var form_data = new FormData();
        form_data.append('video_link', $(element).find('input[name=video_link]').val());
        form_data.append('display_name', $(element).find('input[name=display_name]').val());

        $(this).addClass("disabled");
        $.ajax({
            url: handlerUrl,
            dataType: 'json',
            cache: false,
            contentType: false,
            processData: false,
            data: form_data,
            type: "POST",
            complete: function () {
                $(this).removeClass("disabled");
            },
            success: function (response) {
                if (response.errors.length > 0) {
                    response.errors.forEach(function (error) {
                        runtime.notify("error", {
                            "message": error,
                            "title": "Save failed"
                        });
                    });
                } else {
                    runtime.notify('save', {
                        state: 'end'
                    });
                }
            }
        });
    });

    $(element).find('.cancel-button').bind('click', function () {
        runtime.notify('cancel', {});
    });
}

