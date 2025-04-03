
(function($) {
    $.fn.tabs = function(options) {
        var settings = $.extend({
            defaultTab: 0, // Index of the default tab
            // activeClass: 'active', // Class applied to the active tab
            animation: true, // Enable/disable tab content animation,
            type: 'slide-horizontal',
        }, options);

        return this.each(function() {
            var $tabsContainer = $(this);
            var $tabsNav = $tabsContainer.find('.tabs-nav li');
            var $tabContent = $tabsContainer.find('.tab-content');

            $tabsNav.on('click', function(event) {
                event.preventDefault();
                var targetTab = $(this).find('a').attr('href');

                if (settings.animation) {

                    $tabContent.hide();
                 
                    if (settings.type === 'fade') {
                        $(targetTab).fadeIn();
                    } else if (settings.type === 'slide-horizontal') {
                        console.log('slide-horizontal')
                        $(targetTab).slideDown();
                    } else if (settings.type === 'slide-vertical') {
                        $(targetTab).slideDown();
                    } else if (settings.type === 'slide-swing') {
                        $(targetTab).show('swing');
                    }

                } else {
                    $tabContent.hide();
                    $(targetTab).show();
                }

                $tabsNav.removeClass('active');
                $(this).addClass('active');
            });

            // Show the default tab
            $tabsNav.eq(settings.defaultTab).click();

            $tabsNav.eq(settings.defaultTab).addClass('disabled');
        });
    };
})(jQuery);



