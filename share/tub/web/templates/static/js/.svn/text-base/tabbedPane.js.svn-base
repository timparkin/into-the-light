var is_form_dirty = false;

function setupTabbedPane(data, selectedTab)
{
	if(!selectedTab)
	{
		selectedTab = data[0][0];
	}
	
    for(i=0; i<data.length; i++)
    {
        var tab = document.getElementById(data[i][0]);
        var page = document.getElementById(data[i][1]);
        var form = document.getElementById(data[i][2]);

        if(tab.id == selectedTab)
        {
            tab.className = 'selected'
            page.className = 'selected';
        }
        else
        {
            tab.className = 'not-selected'
            page.className = 'not-selected';
        }

        for(j=0; j<form.elements.length;j++)
        {
            form.elements[j].onchange = function()
            {
                is_form_dirty = true;
            }
        }

        tab.onclick = function()
        {
            if( is_form_dirty )
            {
                response = confirm( 'You have unsaved changes on this tab. Click OK to stay on this tab or click Cancel to switch tabs and lose your changes.' );
                if( response == true )
                {
                    return;
                }
                is_form_dirty = false;
            }
            
            for(i=0; i<data.length; i++)
            {
                tab = document.getElementById(data[i][0]);
                page = document.getElementById(data[i][1]);

                if(tab.id == this.id)
                {
                    tab.className = 'selected';
                    page.className = 'selected';
                }
                else
                {
                    tab.className = 'not-selected';
                    page.className = 'not-selected';
                }
            }
        }
    }
}

function tinyMCEOnChangeHook(inst) {
    is_form_dirty = true;
}
