odoo.define('broken_loyalty.loyalty', function (require) {
    'use strict';
    var Widget = require('web.Widget');
    var Loyalty = Widget.extend({
        start: function () {
            console.log('start');
            var value = this.getParent()?.value;
            this.$el.off('click');
            if (value != null) {
                this.$el.text(value);
            }
            return this._super();
        },
    });
    return Loyalty;
});
