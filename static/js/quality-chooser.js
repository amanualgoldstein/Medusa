$(document).ready(function() {
    function setFromPresets(preset) {
        if (parseInt(preset, 10) === 0) {
            $('#customQuality').show();
            return;
        }

        $('#customQuality').hide();

        $('#allowed_qualities option').each(function() {
            var result = preset & $(this).val();
            if (result > 0) {
                $(this).prop('selected', true);
            } else {
                $(this).prop('selected', false);
            }
        });

        $('#preferred_qualities option').each(function() {
            var result = preset & ($(this).val() << 16);
            if (result > 0) {
                $(this).prop('selected', true);
            } else {
                $(this).prop('selected', false);
            }
        });

        return;
    }

    function backloggedEpisodes() {
        var selectedPreffered = [];
        var selectedAllowed = [];
        $('#preferred_qualities :selected').each(function(i, selected){
            selectedPreffered[i] = $(selected).val();
        });
        $('#allowed_qualities :selected').each(function(i, selected){
            selectedAllowed[i] = $(selected).val();
        });
        var url = '/api/v2/' +
                  'show/' +  $('#showIndexerName').attr('value') + $('#showID').attr('value') +
                  '/backlogged' +
                  '?api_key=' + apiKey +
                  '&allowed=' + selectedAllowed +
                  '&preferred=' + selectedPreffered
        $.getJSON(url, function(data) {
            $('#backlogged_episodes').text('Currently you have ' + data[1] + ' backlogged episodes. With this change you would have ' + data[0] + ' backlogged episodes');
        });
    }

    function setQualityText() {
        var preferred = $.map($('#preferred_qualities option:selected'), function(option) {
            return option.text;
        });
        var allowed = $.map($('#allowed_qualities option:selected'), function(option) {
            return option.text;
        });
        var both = allowed.concat(preferred.filter(function (item) {
            return allowed.indexOf(item) < 0;
        }));

        var allowed_preferred_explanation = both.join(', ');
        var preferred_explanation = preferred.join(', ');
        var allowed_explanation = allowed.join(', ');

        $('#allowed_preferred_explanation').text(allowed_preferred_explanation);
        $('#preferred_explanation').text(preferred_explanation);
        $('#allowed_explanation').text(allowed_explanation);

        $('#allowed_text').hide();
        $('#preferred_text1').hide();
        $('#preferred_text2').hide();
        $('#quality_explanation').show();

        if (preferred.length) {
            $('#preferred_text1').show();
            $('#preferred_text2').show();
        } else if (allowed.length) {
            $('#allowed_text').show();
        } else {
            $('#quality_explanation').hide();
        }
    }

    $('#qualityPreset').on('change', function() {
        setFromPresets($('#qualityPreset :selected').val());
    });

    $('#qualityPreset, #preferred_qualities, #allowed_qualities').on('change', function(){
        setQualityText();
        backloggedEpisodes();
    });

    setFromPresets($('#qualityPreset :selected').val());
    setQualityText();
});
