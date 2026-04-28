# MCP Demo Customization Guide

## Adding Test Elements to Demo Page

The demo page (`frontend/src/pages/AIAssistantDemo.tsx`) contains interactive elements that Claude can control. Here's how to add more:

### 1. Add a New Text Input

```tsx
// In the form, add:
<div className={styles.formGroup}>
  <label className={styles.label}>SKU</label>
  <Input
    data-testid="sku"                    // IMPORTANT: unique testid
    placeholder="Enter SKU code"
    value={demoFormData.sku}
    onChange={(e) => handleInputChange('sku', e.target.value)}
    className={styles.input}
  />
</div>

// Update state:
const [demoFormData, setDemoFormData] = useState({
  productName: '',
  description: '',
  category: '',
  price: '',
  quantity: '',
  sku: '',  // ADD THIS
});
```

Claude can then target it with:
```json
{"tool": "input", "params": {"selector": "[data-testid=sku]", "text": "SKU-12345"}}
```

### 2. Add a Checkbox

```tsx
<div className={styles.formGroup}>
  <label>
    <input
      type="checkbox"
      data-testid="in-stock"
      checked={demoFormData.inStock}
      onChange={(e) => handleInputChange('inStock', e.target.checked)}
    />
    In Stock
  </label>
</div>
```

Claude can target it with:
```json
{"tool": "click", "params": {"selector": "[data-testid=in-stock]"}}
```

### 3. Add a Radio Group

```tsx
<div className={styles.formGroup}>
  <label className={styles.label}>Availability</label>
  <div>
    <label>
      <input
        type="radio"
        name="availability"
        value="available"
        data-testid="availability-available"
        checked={demoFormData.availability === 'available'}
        onChange={(e) => handleInputChange('availability', e.target.value)}
      />
      Available
    </label>
    <label>
      <input
        type="radio"
        name="availability"
        value="backorder"
        data-testid="availability-backorder"
        checked={demoFormData.availability === 'backorder'}
        onChange={(e) => handleInputChange('availability', e.target.value)}
      />
      Backorder
    </label>
  </div>
</div>
```

### 4. Add Action Buttons

```tsx
<div className={styles.buttonGroup}>
  <Button
    type="primary"
    data-testid="publish-btn"        // IMPORTANT: testid
    onClick={handlePublish}
  >
    Publish
  </Button>
  <Button
    data-testid="draft-btn"
    onClick={handleDraft}
  >
    Save as Draft
  </Button>
</div>
```

Claude can click with:
```json
{"tool": "click", "params": {"selector": "[data-testid=publish-btn]"}}
```

### 5. Add Dynamic Content (Table/List)

```tsx
<div className={styles.section}>
  <h3>Products</h3>
  <table data-testid="products-table">
    <thead>
      <tr>
        <th>Name</th>
        <th>Price</th>
        <th>Action</th>
      </tr>
    </thead>
    <tbody>
      {products.map((p) => (
        <tr key={p.id} data-testid={`product-row-${p.id}`}>
          <td>{p.name}</td>
          <td>${p.price}</td>
          <td>
            <button data-testid={`delete-${p.id}`}>Delete</button>
          </td>
        </tr>
      ))}
    </tbody>
  </table>
</div>
```

Claude can interact with:
```json
{"tool": "click", "params": {"selector": "[data-testid=delete-1]"}}
```

## Testing Claude's Ability to Use New Elements

After adding elements, test with these prompts:

```
# Test text input
"Set SKU to ABC-123"

# Test checkbox
"Check the 'In Stock' checkbox"

# Test radio
"Select 'Backorder' from availability"

# Test button
"Click the Publish button"

# Test table interaction
"Delete the first product"

# Complex task
"Fill all product details and publish"
```

## Naming Conventions

- **Always use `data-testid`** for all interactive elements
- **Keep testids lowercase with hyphens**: `product-name`, `submit-btn`, `delete-1`
- **Be descriptive**: `product-name` vs `input1`
- **Group related elements**: `category-select`, `category-option-electronics`
- **Avoid generic names**: Don't use `button1`, `input2`

## CSS Classes

Add to `AIAssistantDemo.module.css`:

```css
.section {
  margin-top: 24px;
  padding: 16px;
  background: #fafafa;
  border-radius: 4px;
}

.section h3 {
  margin-top: 0;
  color: #262626;
}

.checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
}

.radioGroup {
  display: flex;
  gap: 16px;
}

.table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 8px;
}

.table th,
.table td {
  text-align: left;
  padding: 8px;
  border-bottom: 1px solid #d9d9d9;
}

.table th {
  background: #fafafa;
  font-weight: 500;
}
```

## State Management Pattern

```tsx
const [demoFormData, setDemoFormData] = useState({
  // ... existing fields
  sku: '',
  availability: 'available',
  inStock: false,
  tags: [],
});

const handleInputChange = (field: string, value: any) => {
  setDemoFormData(prev => ({
    ...prev,
    [field]: value,
  }));
};
```

## Validation & Feedback

Add real-time validation Claude can verify:

```tsx
const handleFormChange = (field: string, value: string) => {
  setDemoFormData(prev => ({
    ...prev,
    [field]: value,
  }));

  // Add validation
  if (field === 'price' && isNaN(Number(value))) {
    setErrors(prev => ({
      ...prev,
      price: 'Price must be a number',
    }));
  }
};
```

Claude can verify errors appear with:
```
"Try to submit with invalid price (abc) and show error message"
```

## Advanced: Custom Selectors

For complex scenarios, you can create compound selectors:

```tsx
// Nested structure Claude can target
<div className="product-form">
  <fieldset>
    <legend>Basic Info</legend>
    <input data-testid="name" />
    <input data-testid="price" />
  </fieldset>
  <fieldset>
    <legend>Advanced</legend>
    <input data-testid="sku" />
    <input data-testid="weight" />
  </fieldset>
</div>
```

Claude selectors:
```json
// Direct
{"tool": "input", "params": {"selector": "[data-testid=name]", "text": "Product"}}

// Via fieldset (also works)
{"tool": "input", "params": {"selector": "fieldset:first-of-type input[data-testid=name]", "text": "Product"}}
```

## Security Best Practices

✅ **DO:**
- Use descriptive testids: `user-email-input`
- Keep selectors simple and specific
- Validate all user inputs
- Log Claude's tool calls for audit

❌ **DON'T:**
- Use sensitive data in testids
- Expose system paths: `data-testid="/admin/users"`
- Allow script/iframe tags
- Store tokens in demo page

## Performance Tips

1. **Lazy load large lists**: Use virtual scrolling for 100+ items
2. **Debounce input**: Add `lodash/debounce` for real-time validation
3. **Optimize screenshots**: Large form screenshots slow things down
4. **Split into sections**: Break demo into tabs/accordions

## Example: Multi-step Wizard

```tsx
const [currentStep, setCurrentStep] = useState(1);

<div>
  {currentStep === 1 && (
    <div>
      <h3>Step 1: Basic Info</h3>
      <Input data-testid="step1-name" />
      <Button data-testid="next-step" onClick={() => setCurrentStep(2)}>
        Next
      </Button>
    </div>
  )}

  {currentStep === 2 && (
    <div>
      <h3>Step 2: Pricing</h3>
      <Input data-testid="step2-price" />
      <Button data-testid="prev-step" onClick={() => setCurrentStep(1)}>
        Back
      </Button>
      <Button data-testid="submit-all" onClick={handleSubmit}>
        Submit
      </Button>
    </div>
  )}
</div>
```

Claude can navigate:
```
"Fill step 1, click next, then fill step 2 and submit"
```

---

**Questions?** Check `MCP_TOOL_EXAMPLES.md` for more patterns.
