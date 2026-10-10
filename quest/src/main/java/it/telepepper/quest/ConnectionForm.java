package it.telepepper.quest;

import android.app.Activity;
import android.view.WindowManager;
import android.widget.*;
import it.telepepper.ui.StudioStyle;

/** Compact, fixed connection panel; actions stay visible beside credentials. */
final class ConnectionForm {
    static TextView label(StudioStyle ui, String value, int size, int color) {
        return ui.text(value, size >= 24 ? 22 : Math.min(size, 14), color, size >= 24);
    }
    static EditText field(StudioStyle ui, LinearLayout parent, String title, String value, boolean secret) {
        EditText edit = ui.field(parent, title, value, secret);
        TextView label = (TextView) parent.getChildAt(parent.getChildCount()-2);
        label.setTextSize(11);
        LinearLayout.LayoutParams space = (LinearLayout.LayoutParams) label.getLayoutParams();
        space.setMargins(0, ui.dp(6), 0, ui.dp(3)); label.setLayoutParams(space);
        edit.setTextSize(16); edit.setPadding(ui.dp(10), ui.dp(4), ui.dp(10), ui.dp(4));
        edit.getLayoutParams().height = ui.dp(38);
        return edit;
    }
    static LinearLayout.LayoutParams buttonSpace(StudioStyle ui){
        LinearLayout.LayoutParams value=new LinearLayout.LayoutParams(-1,ui.dp(40));
        value.setMargins(0,ui.dp(6),0,0);return value;
    }
    static void show(Activity activity, StudioStyle ui, LinearLayout root, Button enter) {
        enter.setTextSize(15);enter.setText("Open VR");
        LinearLayout.LayoutParams footer=new LinearLayout.LayoutParams(-1,ui.dp(48));
        footer.setMargins(0,ui.dp(10),0,0);root.addView(enter,footer);
        activity.getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE
                | WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_HIDDEN);
        activity.setContentView(root);
    }
}
