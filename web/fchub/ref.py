def fab_calculate_possible_product_count(order_id):
    # Get the ordered items for the given order_id
    
    

    # Collect fabric names and colors from the ordered items


    for item in order_items:
        fabric_names.add(item.product.category.fabric)
        fabric_colors.add(item.product.color.lower())  # Lowercase for consistency

    # Retrieve available fabric materials based on ordered fabric names and colors
    

    # Cross-reference fabric materials with CurtainIngredients to find required details
    # Assuming 'fabric_name' in CurtainIngredients matches 'fabric_name' in FabricMaterial
    

    # Fetch available thread materials based on the fabric and color
    

    # Calculate required fabric counts
    required_fabric_count = curtain_ingredients.aggregate(Sum('fabric_count'))['fabric_count__sum']

    # Calculate required thread counts
    required_thread_count = curtain_ingredients.aggregate(Sum('thread_count'))['thread_count__sum']

    # Assuming the 'grommet' and 'rings' are specified in the CurtainIngredients model directly
    required_grommet_count = curtain_ingredients.aggregate(Sum('grommet_count'))['grommet_count__sum']
    required_rings_count = curtain_ingredients.aggregate(Sum('rings_count'))['rings_count__sum']

    # Now you can process and calculate the possible product count based on these details

    max_possible_fabric = available_fabrics.aggregate(Sum('fabric_fcount'))['fabric_fcount__sum'] // required_fabric_count
    max_possible_thread = available_threads.aggregate(Sum('count'))['count__sum'] // required_thread_count
    max_possible_grommet = curtain_ingredients.aggregate(Sum('grommet_count'))['grommet_count__sum'] // required_grommet_count
    max_possible_rings = curtain_ingredients.aggregate(Sum('rings_count'))['rings_count__sum'] // required_rings_count



    max_possible_product_count = min(max_possible_fabric, max_possible_thread, max_possible_grommet, max_possible_rings)

    # List the materials needed for creating the product
    materials_needed = {
        'Fabric': required_fabric_count,
        'Thread': required_thread_count,
        'Grommet': required_grommet_count,
        'Rings': required_rings_count,
    }

    return max_possible_product_count, materials_needed