import json

def main():
    state_path = "/Users/xaa/zuoye/oneform/kuokka add/react_structure.json"
    with open(state_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    layers = data.get("layers", [])
    
    # Let's inspect Layer 4: r (has 'task' in State)
    # and Layer 5: n (has 'task' in Props)
    for idx, layer in enumerate(layers):
        type_name = layer.get('type')
        print(f"\n======================================")
        print(f"LAYER {idx+1}: {type_name}")
        print(f"======================================")
        
        # Check Props
        props = layer.get('props') or {}
        if 'task' in props:
            print("\nFOUND 'task' in PROPS:")
            print(json.dumps(props['task'], indent=2, ensure_ascii=False))
            
        # Check State
        state = layer.get('state') or {}
        if 'task' in state:
            print("\nFOUND 'task' in STATE:")
            print(json.dumps(state['task'], indent=2, ensure_ascii=False))
            
        if 'uiState' in state:
            print("\nFOUND 'uiState' in STATE (Layer state):")
            # Only print keys or summary of uiState to not clutter
            print("Keys:", list(state.keys()))
            if 'annotations' in state:
                print("Annotations:", state['annotations'])
            if 'videoSource' in state:
                print("videoSource:", state['videoSource'])

if __name__ == "__main__":
    main()
