import Alert from "./components/Alert";
import ListGroup from "./components/ListGroup";
import Button from "./components/button";
import { useState } from "react";
function App() {
  let items = ["New York", "San Francisco", "Tokyo", "London", "Paris"];
  const [alertVisible, setAlertVisible] = useState(false);

  const handleSelectItem = (item: string) => {
    console.log(item);
  };
  return (
    <div>
      <ListGroup
        items={items}
        heading="Cities"
        onSelectItem={handleSelectItem}
      />
      {alertVisible && (
        <Alert onClose={() => setAlertVisible(false)}>My alert</Alert>
      )}
      <Button color="danger" onClick={() => setAlertVisible(true)}>
        My Button
      </Button>
    </div>
  );
}
export default App;
