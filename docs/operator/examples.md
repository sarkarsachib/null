# Operator Examples

This collection demonstrates common workload patterns for Null-Lang applications.

## 1. Chatbot Service

A simple HTTP service that uses the NLP module to respond to user queries.

```null
@require(std, nlp, net)

use std::net::HttpServer;
use nlp::ChatModel;

async fn handle_request(req: Request) -> Response {
    let model = ChatModel::load("gpt-mini");
    let user_input = req.body.text;
    let response = await model.generate(user_input);
    return Response::json({ "reply": response });
}

fn main() {
    let server = HttpServer::new();
    server.post("/chat", handle_request);
    server.listen(8080);
}
```

## 2. Data Pipeline

ETL process that reads from a file, transforms data, and writes to a database.

```null
@require(std, data)

use std::io::{File, Reader};
use data::DataFrame;

fn main() {
    // Extract
    let raw_data = File::read_csv("input_data.csv");
    let df = DataFrame::from(raw_data);

    // Transform
    let clean_df = df
        .filter(|row| row.age > 18)
        .map(|row| {
            row.name = row.name.to_upper();
            return row;
        });

    // Load
    clean_df.write_sql("postgres://db:5432/users", "clean_users");
}
```

## 3. ML Training Loop

Training a simple neural network using the ML module.

```null
@require(ml)

use ml::{Tensor, Module, Optimizer, Loss};

class SimpleNet extends Module {
    fn init() {
        self.fc1 = ml::Linear(10, 5);
        self.fc2 = ml::Linear(5, 1);
    }

    fn forward(x: Tensor) -> Tensor {
        x = self.fc1(x).relu();
        return self.fc2(x);
    }
}

fn main() {
    let model = SimpleNet();
    let optimizer = Optimizer::SGD(model.parameters(), lr=0.01);
    let criterion = Loss::MSE();

    for epoch in 0..100 {
        let (data, target) = get_batch();
        
        optimizer.zero_grad();
        let output = model(data);
        let loss = criterion(output, target);
        loss.backward();
        optimizer.step();

        println!("Epoch {epoch}: Loss = {loss.item()}");
    }
}
```

## 4. Optimization Workload

Using the optimization module to solve a linear programming problem.

```null
@require(opt)

use opt::{Solver, Variable, Constraint};

fn main() {
    let solver = Solver::new("minimize");

    // Variables
    let x = Variable::continuous("x", min=0);
    let y = Variable::continuous("y", min=0);

    // Objective: Minimize 2x + 3y
    solver.set_objective(2*x + 3*y);

    // Constraints
    solver.add_constraint(x + y >= 10);
    solver.add_constraint(x - y <= 5);

    // Solve
    let result = solver.solve();
    
    if result.success {
        println!("Solution: x={x.value()}, y={y.value()}");
    } else {
        println!("No solution found");
    }
}
```
