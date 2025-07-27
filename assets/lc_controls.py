
# Control components["control_panel"]
cp_center = [-machine.x / 2, machine.y / 2, machine.z / 2 - 100]
components["control_panel"] = box(extents=[150, material_thickness, 80])
components["control_panel"].apply_translation(cp_center)
add_texture(components["control_panel"], "panel.jpg")

# Control buttons
buttons = []
button_count = 5
for i in range(button_count):
    button = cylinder(
        radius=5,
        height=30,
    )
    button.apply_transform(ccrotation1)
    button.apply_translation(cp_center)
    button.apply_translation([i * 15 - 15 * (button_count / 2.0), 0, 0])
    add_texture(button, "red.jpg")
    buttons.append(button)

# Display
components["display"] = box(
    extents=[60, 2, 30],
)
components["display"].apply_translation(cp_center)
components["display"].apply_translation([0, 0, -1])
add_texture(components["display"], "lcd.png")
components["buttons_mesh"] = trimesh.util.concatenate(buttons)
